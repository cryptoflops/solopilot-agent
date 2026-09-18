"""
SoloPilot agent built on the AWS Strands Agents SDK.

A "Professional Agent" for Solana wallet recon: given any base58 address it
quietly pulls the boring on-chain facts (is it a mint? who holds it? what's
the balance? is this tx landable?) and surfaces only the decoded picture as a
triage note. All chain reads go through permissionless public Solana
JSON-RPC; the LLM plans the calls, the runtime executes them.

Model: Gemini via Strands' GeminiModel (swap provider with one line).
"""

import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "mock-key")

MODEL_ID = os.environ.get("SOLOPILOT_MODEL", "gemini-flash-lite-latest")
SOLANA_RPCS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
]

# SPL Mint account data is 82 bytes: [4:36] mint_authority, [36:44] supply u64 LE, [44] decimals, [50:82] freeze_authority
MINT_LEN = 82

SYSTEM_PROMPT = (
    "You are SoloPilot, an autonomous on-chain recon agent for Solana. "
    "Given a base58 address, wallet, or mint: inspect it with the "
    "solana_get_account, solana_balance and solana_token_balances tools, "
    "decode results, and write a concise triage note with write_file. Use "
    "tools for every chain fact; never fabricate addresses, owners, or "
    "values. If getAccountInfo returns null, say the address has no account."
)


def _sol_http(method: str, params: list) -> dict:
    """JSON-RPC with mainnet-beta -> publicnode fallback. Returns parsed response."""
    import requests
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    for rpc in SOLANA_RPCS:
        try:
            j = requests.post(rpc, json=payload, timeout=10).json()
            if "result" in j or "error" in j:
                return {"rpc": rpc, **j}
        except Exception:
            continue
    return {"error": "all RPCs unreachable"}


def _token_meta(mint: str) -> dict:
    """Name/symbol from Jupiter's keyless token API; {} on any failure -
    metadata is decoration, never a blocker for the chain facts."""
    try:
        import requests
        r = requests.get(
            "https://lite-api.jup.ag/tokens/v2/search",
            params={"query": mint}, timeout=5).json()
        t = next((x for x in r if x.get("id") == mint), None)
        return {"name": t["name"], "symbol": t["symbol"]} if t else {}
    except Exception:
        return {}


def _decode_mint(parsed: dict, mint: str) -> dict:
    info = parsed["parsed"]["info"]
    out = {"supply": int(info["supply"]), "decimals": info["decimals"],
           "mint_authority": info.get("mintAuthority"),
           "freeze_authority": info.get("freezeAuthority")}
    out.update(_token_meta(mint))
    return out


def build_agent():
    """Wire a Strands Agent with the on-chain tool set."""
    from strands import Agent, tool
    from strands.models.gemini import GeminiModel

    @tool
    def solana_get_account(address: str) -> str:
        """getAccountInfo for a base58 address: lamports, owner program,
        data size. Mint accounts are owned by TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
        and 82 bytes long; decoded mint fields are included when applicable."""
        r = _sol_http("getAccountInfo", [address, {"encoding": "jsonParsed"}])
        val = (r.get("result") or {}).get("value")
        if val is None:
            return json.dumps(r)
        data = val["data"]
        out = {
            "lamports": val["lamports"],
            "sol": val["lamports"] / 1e9,
            "owner": val["owner"],
        }
        if isinstance(data, dict) and data.get("program") == "spl-token":
            out["parsed_type"] = data["parsed"]["type"]
            if data["parsed"]["type"] == "mint":
                out["mint"] = _decode_mint(data, address)
        else:
            out["data_len"] = len(base64.b64decode(data[0])) if data else 0
        return json.dumps({"address": address, **out})

    @tool
    def solana_balance(address: str) -> str:
        """SOL balance (getBalance) of a wallet in lamports and SOL."""
        return json.dumps(_sol_http("getBalance", [address, {"commitment": "confirmed"}]))

    @tool
    def solana_token_balances(address: str) -> str:
        """All SPL token holdings of a wallet (getTokenAccountsByOwner),
        with mint, ui amount and decimals."""
        r = _sol_http("getTokenAccountsByOwner", [address, {
            "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed", "commitment": "confirmed"}])
        accts = (r.get("result") or {}).get("value", [])
        return json.dumps([
            {"mint": a["account"]["data"]["parsed"]["info"]["mint"],
             "ui_amount": a["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"],
             "decimals": a["account"]["data"]["parsed"]["info"]["tokenAmount"]["decimals"]}
            for a in accts])

    @tool
    def solana_recent_perf() -> str:
        """Chain health snapshot: latest blockhash + transaction count."""
        bh = _sol_http("getLatestBlockhash", [{"commitment": "confirmed"}])
        tc = _sol_http("getTransactionCount", [{"commitment": "confirmed"}])
        return json.dumps({
            "blockhash": (bh.get("result") or {}).get("value", {}).get("blockhash"),
            "tx_count": tc.get("result"),
        })

    @tool
    def read_file(path: str) -> str:
        """Read a text file from the workspace."""
        with open(path) as f:
            return f.read()

    @tool
    def write_file(path: str, content: str) -> str:
        """Write a triage note to the workspace."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"wrote {len(content)} chars to {path}"

    model = GeminiModel(model_id=MODEL_ID)  # API key picked up from GEMINI_API_KEY env
    return Agent(
        model=model,
        tools=[solana_get_account, solana_balance, solana_token_balances,
               solana_recent_perf, read_file, write_file],
        system_prompt=SYSTEM_PROMPT,
    )


def run_reasoning_loop(prompt: str) -> dict:
    """Execute agent; return final text + tool trace from agent.messages."""
    agent = build_agent()
    result = agent(prompt)
    steps = []
    for msg in getattr(agent, "messages", []):
        for c in (msg.get("content") if isinstance(msg.get("content"), list) else []):
            if "toolUse" in c:
                steps.append({"role": "tool_call",
                              "content": json.dumps({"tool": c["toolUse"].get("name"),
                                                     "args": c["toolUse"].get("input")})})
            if "toolResult" in c:
                body = "".join(p.get("text", "") for p in c["toolResult"].get("content", []))
                steps.append({"role": "tool_result", "content": body[:2048]})
    return {"output": str(result), "steps": steps}


if __name__ == "__main__":
    # live check: USDC mint must parse, decimals == 6
    _USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    v = (_sol_http("getAccountInfo", [_USDC, {"encoding": "jsonParsed"}]).get("result") or {}).get("value")
    m = _decode_mint(v["data"], _USDC)
    assert m["decimals"] == 6 and m.get("symbol") == "USDC", f"USDC decode failed: {m}"
    print(f"ok: USDC decimals=6, supply={m['supply']/1e6:,.0f}, mint_authority={m['mint_authority']}")
