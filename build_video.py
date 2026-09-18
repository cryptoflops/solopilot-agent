#!/usr/bin/env python3
"""SoloPilot demo video: HTML slides -> headless Chrome -> edge-tts -> ffmpeg,
with the real Playwright console recording (2 runs) as the centerpiece.
Narration numbers are read off the recording frames, not invented.
Usage: python3 build_video.py   (record_ui.py must have run first)"""
import subprocess, os, sys, asyncio, glob
import edge_tts

WORK = "/tmp/sp-video"; REC = "/tmp/sp-rec/video.webm"
os.makedirs(WORK, exist_ok=True)
W, H = 1920, 1080
VOICE = "en-US-AndrewMultilingualNeural"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = os.path.expanduser("~/Projects/hackathons/solopilot/solopilot_demo.mp4")

CSS = """
* { margin:0; padding:0; box-sizing:border-box }
body { width:1920px; height:1080px; background:#0b0e14; color:#e6eaf2;
  font-family:-apple-system,'Helvetica Neue',sans-serif; overflow:hidden }
.slide { width:100%; height:100%; padding:90px 110px; display:flex; flex-direction:column }
h1 { font-size:96px; font-weight:800; letter-spacing:-2px }
h2 { font-size:64px; font-weight:750; margin-bottom:36px; letter-spacing:-1px }
.accent { color:#7ee2b8 }
.dim { color:#8a93a6 }
.big { font-size:44px; line-height:1.5 }
.mid { font-size:36px; line-height:1.6 }
.mono { font-family:'SF Mono',Menlo,monospace }
pre { font-family:'SF Mono',Menlo,monospace; font-size:27px; line-height:1.55;
  background:#0f1420; border:1px solid #1d2635; border-radius:14px; padding:34px 40px;
  white-space:pre-wrap; color:#c9d4e6 }
.hl { color:#8ecbff } .warn { color:#f2c94c } .ok { color:#7ee2b8 }
.row { display:flex; gap:26px } .card { flex:1; background:#0f1420; border:1px solid #1d2635;
  border-radius:14px; padding:34px } .card b { display:block; font-size:34px; margin-bottom:14px }
.card span { font-size:28px; color:#9aa5b8; line-height:1.45; display:block }
.center { justify-content:center } .foot { margin-top:auto; font-size:26px; color:#57607a }
"""

SLIDES = {
 "01-title": f"""<div class="slide center">
  <h1><span class="accent">SoloPilot</span></h1>
  <p class="big" style="margin-top:26px">An autonomous Solana triage agent, built on<br><b style="color:#fff">the AWS Strands Agents SDK</b></p>
  <p class="mid dim" style="margin-top:30px">Colosseum Crypto World's Fair · Superteam Ukraine track</p>
  <p class="foot">github.com/cryptoflops/solopilot-agent</p></div>""",

 "02-problem": f"""<div class="slide"><h2>Before you touch an address, you ask <span class="accent">what is it</span></h2>
  <pre class="mono" style="font-size:31px">a mint? who holds <span class="warn">mint authority</span>? can it <span class="warn">freeze your balance</span>?
a wallet? what does it actually hold?

today: explorer tabs, account data you have to decode by eye
same ten minutes, every new token, every new counterparty</pre>
  <p class="mid dim" style="margin-top:34px">SoloPilot reads the chain and leaves you a note.</p></div>""",

 "03-how": f"""<div class="slide"><h2>One address. <span class="accent">The agent plans the reads.</span></h2>
  <div class="row" style="margin-top:10px">
   <div class="card"><b>inspect</b><span>getAccountInfo jsonParsed: type, owner, supply, decimals, authorities</span></div>
   <div class="card"><b>holdings</b><span>getBalance + getTokenAccountsByOwner: SOL and every SPL token it holds</span></div>
   <div class="card"><b>artifact</b><span>writes notes/triage.md, then re-reads the file to verify it landed</span></div></div>
  <p class="mid" style="margin-top:36px">Live mainnet over <span class="accent">public RPC, zero chain API keys</span>. The system prompt bans fabricated chain facts: every number on screen is a tool result.</p></div>""",

 "08-strands": f"""<div class="slide"><h2>Under the hood: <span class="accent">Strands Agents SDK</span></h2>
  <pre class="mono">from strands import Agent, tool
from strands.models.gemini import GeminiModel

<span class="hl">@tool</span> def solana_get_account(address)     <span class="dim"># jsonParsed; mint fields decoded</span>
<span class="hl">@tool</span> def solana_balance(address)          <span class="dim"># lamports + SOL</span>
<span class="hl">@tool</span> def solana_token_balances(address)   <span class="dim"># every SPL holding</span>
<span class="hl">@tool</span> def solana_recent_perf()             <span class="dim"># blockhash + tx count</span>
<span class="hl">@tool</span> def read_file / write_file           <span class="dim"># the artifact and its proof</span>

agent = Agent(model=GeminiModel(...), tools=[...], system_prompt=SYSTEM_PROMPT)</pre>
  <p class="mid dim" style="margin-top:24px">The SDK loop does planning, dispatch, retries. Custom part: tool discipline. Fallback RPCs, raw response kept beside every decoded value. Swapping the model is one line.</p></div>""",

 "09-limits": f"""<div class="slide"><h2>Scope, and what's next</h2>
  <div class="row">
   <div class="card"><b>today</b><span>one address per run. read-only by design, so there is no spending authority to trust yet</span></div>
   <div class="card"><b>next</b><span>Jupiter price cross-check so holdings show in dollars, then batch mode over a watchlist</span></div>
   <div class="card"><b>later</b><span>an agent that pays for premium data itself, x402 payment channels fit this loop</span></div></div>
  <p class="mid" style="margin-top:40px">All chain reads stay keyless public RPC.</p></div>""",

 "10-close": f"""<div class="slide center">
  <h1><span class="accent">SoloPilot</span></h1>
  <p class="big" style="margin-top:24px">Clone it, run it against mainnet.<br>The agent writes its own proof.</p>
  <p class="big mono hl" style="margin-top:46px">github.com/cryptoflops/solopilot-agent</p>
  <p class="foot">Strands Agents SDK · MIT · built for Colosseum Crypto World's Fair</p></div>""",
}

# narration numbers verified against recording frames:
# run1: 2 passes, 5.2s loop, supply 7,684,468,333.21, 6 decimals, BJE5../7dGb..
# run2: 4 passes, 4.6s loop, multisig, 6 token accounts, 0.055633622 SOL
NARR = {
 "01-title": "This is SoloPilot. An autonomous Solana triage agent on the AWS Strands Agents SDK, built for the Colosseum Crypto World's Fair.",
 "02-problem": "Before you interact with any Solana address you want to know what it is. Is it a mint, and who holds mint and freeze authority. Is it a wallet, and what does it actually hold. Today that means explorer tabs and decoding account data by eye. SoloPilot does the reading and leaves you a note.",
 "03-how": "You give it an address. The agent picks its own tools. Get account info, parse the mint layout, read balances, list every token holding, check chain health. It writes a triage note, then reads the file back to prove it landed. All of it over public RPC, zero chain API keys. The system prompt bans made up chain facts.",
 "05-demo1": "This is the real console, one take. First the USDC mint. Two tool passes, five seconds. The note decodes the supply at seven point six eight billion, six decimals, and both authorities, mint authority starting B J E 5, freeze authority present.",
 "06-demo2": "Then reset, and triage that mint authority itself. Four passes, four point six seconds. The first run surfaced this address as the mint authority. The second follows it, and finds it is not a normal wallet. It is an SPL multisig holding six token accounts. That connection came from reading the chain.",
 "08-strands": "Under the hood it is pure Strands. Six tool functions, a system prompt, and the SDK loop doing planning, dispatch, and retries. The custom part is tool discipline: parsed decoding, fallback RPCs, the raw response kept next to every number. Swapping Gemini for another model is one line.",
 "09-limits": "What it does not do yet: no transaction history, no prices, no batch mode. Next is a Jupiter price cross-check so holdings show in dollars, then a watchlist run. It stays read only by design, so there is no spending authority to trust.",
 "10-close": "Clone it, run it against mainnet, and the agent writes its own proof. SoloPilot. Thanks for watching.",
}
ORDER = ["01-title", "02-problem", "03-how", "05-demo1", "06-demo2", "08-strands", "09-limits", "10-close"]
DEMO = {"05-demo1": (1.6, 11.8), "06-demo2": (11.8, None)}  # webm windows, skip pre-nav white

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-800:]); sys.exit(1)
    return r.stdout.strip()

def dur(p): return float(run(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0',p]))

async def tts():
    for name in ORDER:
        await edge_tts.Communicate(NARR[name], VOICE, rate="+4%").save(f"{WORK}/{name}.mp3")

def main():
    for name, html in SLIDES.items():
        p = f"{WORK}/{name}.html"
        open(p, "w").write(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>")
        run([CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             f"--screenshot={WORK}/{name}.png", f"--window-size={W},{H}", f"file://{p}"])
    asyncio.run(tts())

    parts = []
    for name in ORDER:
        ad = dur(f"{WORK}/{name}.mp3") + 0.7
        mp4 = f"{WORK}/v_{name}.mp4"
        if name in DEMO:
            ss, to = DEMO[name]
            args = ['-ss', str(ss)]
            if to: args += ['-t', str(to - ss)]
            rec_d = (to - ss) if to else dur(REC) - ss
            pad = max(0, ad - rec_d) + 0.01
            seg = max(rec_d + pad, ad)
            run(['ffmpeg','-y','-loglevel','error', *args, '-i', REC,
                 '-i', f"{WORK}/{name}.mp3",
                 '-filter_complex', f"[0:v]tpad=stop_mode=clone:stop_duration={pad:.2f},scale=1920:1080,fps=30[v];[1:a]apad[a]",
                 '-map','[v]','-map','[a]','-t',f"{seg:.2f}",
                 '-c:v','libx264','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','128k','-ar','48000','-ac','2', mp4])
        else:
            run(['ffmpeg','-y','-loglevel','error','-loop','1','-framerate','30','-i',f"{WORK}/{name}.png",
                 '-i', f"{WORK}/{name}.mp3", '-t', f"{ad:.2f}",
                 '-c:v','libx264','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','128k','-ar','48000','-ac','2',
                 '-shortest','-vf','scale=1920:1080', mp4])
        parts.append(mp4)
    open(f"{WORK}/list.txt","w").write("\n".join(f"file '{p}'" for p in parts))
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',f"{WORK}/list.txt",'-c','copy', OUT])
    print("WROTE", OUT, os.path.getsize(OUT)//1024, "KB", f"{dur(OUT):.0f}s")

main()
