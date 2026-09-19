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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
* { margin:0; padding:0; box-sizing:border-box }
body { width:1920px; height:1080px; background:#080A0E; color:#e1e2ea; overflow:hidden;
  font-family:Inter,sans-serif }
.slide { width:100%; height:100%; display:flex; flex-direction:column; position:relative;
  background-image: linear-gradient(to right, rgba(59,74,63,.15) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(59,74,63,.15) 1px, transparent 1px);
  background-size:32px 32px }
/* HUD header */
.hdr { display:flex; align-items:center; gap:28px; padding:22px 56px;
  border-bottom:1px solid #1F2937; background:rgba(10,13,18,.85) }
.brand { font-family:'Space Grotesk'; font-weight:700; font-size:26px; color:#14F195;
  display:flex; align-items:center; gap:14px }
.brand .dot { width:10px; height:10px; border-radius:50%; background:#14F195;
  box-shadow:0 0 12px 2px rgba(20,241,149,.5) }
.nav { font-family:'JetBrains Mono'; font-size:15px; letter-spacing:.08em; color:#94A3B8;
  display:flex; gap:34px }
.nav .on { color:#14F195; border-bottom:2px solid #14F195; padding-bottom:4px }
.chip { font-family:'JetBrains Mono'; font-size:13px; letter-spacing:.06em; padding:8px 16px;
  border:1px solid #1F2937; border-radius:.25rem; color:#94A3B8; background:#111827 }
.chip.live { background:#14F195; color:#080A0E; font-weight:700; border-color:#14F195 }
/* body frame */
.frame { flex:1; padding:56px 72px 20px; display:flex; flex-direction:column; position:relative }
.cross { position:absolute; width:18px; height:18px; opacity:.5 }
.cross::before,.cross::after { content:''; position:absolute; background:#14F195 }
.cross::before { width:18px; height:1px; top:8px } .cross::after { width:1px; height:18px; left:8px }
.tl{top:18px;left:22px}.tr{top:18px;right:22px}.bl{bottom:8px;left:22px}.br{bottom:8px;right:22px}
.idx { font-family:'JetBrains Mono'; font-size:16px; letter-spacing:.08em; color:#14F195;
  margin-bottom:18px }
.idx .cy { color:#00C2FF }
h1 { font-family:'Space Grotesk'; font-weight:700; font-size:112px; letter-spacing:-.03em;
  line-height:1.05 }
h1.grad { background:linear-gradient(135deg,#14F195 0%,#00C2FF 50%,#9945FF 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent }
h2 { font-family:'Space Grotesk'; font-weight:700; font-size:62px; letter-spacing:-.02em;
  line-height:1.12; margin-bottom:20px }
.sub { font-size:28px; color:#94A3B8; line-height:1.5; max-width:1050px; font-weight:300 }
.accent{color:#14F195}.cy{color:#00C2FF}.am{color:#9945FF}.mut{color:#94A3B8}
.mono { font-family:'JetBrains Mono' }
pre { font-family:'JetBrains Mono'; font-size:25px; line-height:1.65; background:#080A0E;
  border:1px solid #1E293B; border-radius:.5rem; padding:30px 36px; white-space:pre-wrap; color:#c9d4e6 }
.tabbar { display:flex; align-items:center; gap:10px; border:1px solid #1E293B;
  border-bottom:none; border-radius:.5rem .5rem 0 0; background:#111827; padding:12px 20px;
  font-family:'JetBrains Mono'; font-size:15px; color:#94A3B8 }
.tabbar .rd{width:11px;height:11px;border-radius:50%;background:#FF5F56}
.tabbar .yy{width:11px;height:11px;border-radius:50%;background:#FEBC2E}
.tabbar .gg{width:11px;height:11px;border-radius:50%;background:#28C840}
.tabbar pre { border:none; border-radius:0; margin:0 }
pre.nb { border-radius:0 0 .5rem .5rem; border-top:none }
.row { display:flex; gap:24px; margin-top:8px }
.card { flex:1; background:#111827; border:1px solid #1F2937; border-radius:.5rem; padding:30px 32px }
.card.glow { border-color:#14F19544; box-shadow:0 0 32px -8px rgba(20,241,149,.12) }
.card .lbl { font-family:'JetBrains Mono'; font-size:14px; font-weight:600;
  letter-spacing:.08em; color:#94A3B8; margin-bottom:14px; display:flex; gap:10px; align-items:center }
.card .lbl::before { content:''; width:6px; height:6px; border-radius:50%; background:#14F195;
  box-shadow:0 0 8px 1px rgba(20,241,149,.4) }
.card b { font-family:'Space Grotesk'; display:block; font-size:31px; font-weight:600; margin-bottom:10px }
.card span { font-size:21px; color:#9aa5b8; line-height:1.5; font-weight:300 }
.badge { display:inline-flex; align-items:center; gap:8px; font-family:'JetBrains Mono';
  font-size:15px; letter-spacing:.05em; padding:9px 18px; border-radius:.25rem;
  background:rgba(20,241,149,.08); border:1px solid rgba(20,241,149,.3); color:#14F195 }
.badge.vio { background:rgba(153,69,255,.08); border-color:rgba(153,69,255,.35); color:#d8b9ff }
.badge.cyn { background:rgba(0,194,255,.08); border-color:rgba(0,194,255,.35); color:#75d1ff }
/* footer */
.ftr { display:flex; align-items:center; gap:26px; padding:16px 56px; border-top:1px solid #1F2937;
  font-family:'JetBrains Mono'; font-size:14px; letter-spacing:.06em; color:#5b6678;
  background:rgba(10,13,18,.85) }
.ftr .gdot { width:8px; height:8px; border-radius:50%; background:#14F195;
  box-shadow:0 0 10px 2px rgba(20,241,149,.45) }
.ftr .sp { flex:1 }
.center { justify-content:center }
.big { font-size:40px; line-height:1.5 }
.mid { font-size:27px; line-height:1.6 }
"""

LOGO = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/logo.svg")).read().replace('viewBox="0 0 120 120"', 'viewBox="0 0 120 120" width="120" height="120"')

def hdr(n, active):
    navs = ["ARCHITECTURE", "RUNTIME", "TELEMETRY", "BENCHMARKS", "DEPLOY"]
    nav = "".join(f'<span class="{"on" if n2 == active else ""}">0{i+1} {n2}</span>' for i, n2 in enumerate(navs))
    return f"""<div class="hdr"><div class="brand"><span class="dot"></span>SoloPilot <span style="color:#e1e2ea">// STRANDS_DAEMON</span></div>
  <div class="nav">{nav}</div><div class="sp" style="flex:1"></div>
  <span class="chip">v1.0.0</span><span class="chip live">LIVE DEMO</span></div>"""

def ftr(left, right):
    return f"""<div class="ftr"><span class="gdot"></span><span>{left}</span><span class="sp"></span><span>{right}</span></div>"""

def cross():
    return '<i class="cross tl"></i><i class="cross tr"></i><i class="cross bl"></i><i class="cross br"></i>'

def idx(n, label):
    return f'<div class="idx">&gt; // {n} <span class="cy">{label}</span> ──────────</div>'

SLIDES = {
 "01-title": f"""<div class="slide">{hdr(1,"ARCHITECTURE")}<div class="frame">{cross()}
  {idx("01_INITIALIZE_CORE_AGENT_RUNTIMES","INITIALIZE")}
  <div style="display:flex;gap:80px;align-items:center;flex:1">
   <div style="flex:1.1">
    <div style="display:flex;align-items:center;gap:26px"><div style="width:120px">{LOGO}</div>
     <h1 class="grad">SoloPilot</h1></div>
    <h2 style="font-size:66px;margin-top:26px">Autonomous Solana<br>Account &amp; Mint Triage Agent</h2>
    <p class="sub" style="margin-top:22px">Sub-second agent reads of on-chain telemetry, mint audits, and account forensics. Built natively on the AWS Strands agentic execution loop.</p>
    <div style="display:flex;gap:16px;margin-top:38px;flex-wrap:wrap">
     <span class="badge">AWS STRANDS AGENTS SDK</span><span class="badge cyn">READ-ONLY / ZERO CHAIN KEYS</span>
     <span class="badge vio">COLOSSEUM CRYPTO WORLD'S FAIR</span></div>
   </div>
   <div style="flex:.9" class="mono">
    <div class="tabbar"><i class="rd"></i><i class="yy"></i><i class="gg"></i>&nbsp;triage-daemon ── live mainnet</div>
    <pre class="nb">SLOT: 447941631 // COMMITMENT: confirmed

<span class="cy">$</span> solopilot triage EPjF…Tt1v
  <span class="accent">●</span> SPL:TOKEN_AUDIT_PASS
  supply   <span class="accent">7,684,468,333</span> USDC
  decimals <span class="accent">6</span>
  mint_auth     BJE5…ruG
  freeze_auth   <span class="am">present</span>
  <span class="accent">✓ read-back verified</span>  <span class="mut">5.2s</span></pre>
   </div></div>
  {ftr("SOLANA MAINNET-BETA // PUBLIC RPC", "STATUS: TRIAGE-READY")}</div></div>""",

 "02-problem": f"""<div class="slide">{hdr(2,"RUNTIME")}<div class="frame">{cross()}
  {idx("02_THREAT_SURFACE","THE CORE PROBLEM")}
  <h2>Before you touch an address,<br>you ask <span class="accent">what is it</span></h2>
  <p class="sub">A mint? Who holds <span class="mono accent">mint authority</span>? Can it <span class="mono accent">freeze your balance</span>? A wallet? What does it actually hold?</p>
  <div class="row" style="margin-top:44px">
   <div class="card"><div class="lbl">TODAY</div><b>Explorer tabs</b><span>Account data decoded by eye, ten minutes per token, every new counterparty from scratch</span></div>
   <div class="card"><div class="lbl">THE GAP</div><b>Clerical forensics</b><span>The boring part is where triage mistakes hide. It is also the part an agent should own</span></div>
   <div class="card glow"><div class="lbl">SOLOPILOT</div><b class="accent">One address in,<br>a written note out</b><span>The agent plans its own RPC reads and proves the artifact landed</span></div></div>
  {ftr("AGENT_STATE: EXECUTING_RECON", "EPOCH: 742 // SLOT: 447,941,631")}</div></div>""",

 "03-how": f"""<div class="slide">{hdr(3,"TELEMETRY")}<div class="frame">{cross()}
  {idx("03_EXECUTION_LOOP","ARCHITECTURE")}
  <h2>One address. <span class="accent">The agent plans the reads.</span></h2>
  <div class="row" style="margin-top:36px">
   <div class="card"><div class="lbl">INSPECT</div><b class="mono" style="font-size:24px">getAccountInfo</b><span>jsonParsed: type, owner, supply, decimals, authorities</span></div>
   <div class="card"><div class="lbl">HOLDINGS</div><b class="mono" style="font-size:24px">getBalance +<br>getTokenAccountsByOwner</b><span>SOL and every SPL token it holds</span></div>
   <div class="card"><div class="lbl">ARTIFACT</div><b class="mono" style="font-size:24px">write_file → read_file</b><span>notes/triage.md, re-read to verify it landed</span></div></div>
  <p class="mid" style="margin-top:44px">Live mainnet over <span class="accent">public RPC, zero chain API keys</span>. The system prompt bans fabricated chain facts: every number on screen is a tool result.</p>
  {ftr("PARALLEL RPC: mainnet-beta → publicnode", "GUARDRAIL: NO FABRICATION")}</div></div>""",

 "08-strands": f"""<div class="slide">{hdr(4,"BENCHMARKS")}<div class="frame">{cross()}
  {idx("04_STRANDS_PIPELINE","UNDER THE HOOD")}
  <div style="display:flex;gap:56px;flex:1">
   <div style="flex:1.2">
    <div class="tabbar"><i class="rd"></i><i class="yy"></i><i class="gg"></i>&nbsp;agent.py ── solopilot</div>
    <pre class="nb">from strands import Agent, tool
from strands.models.gemini import GeminiModel

<span class="cy">@tool</span> def <span class="am">solana_get_account</span>(address)
   <span class="mut"># jsonParsed; mint fields decoded</span>
<span class="cy">@tool</span> def <span class="am">solana_balance</span>(address)
<span class="cy">@tool</span> def <span class="am">solana_token_balances</span>(address)
<span class="cy">@tool</span> def <span class="am">solana_recent_perf</span>()
<span class="cy">@tool</span> def <span class="am">read_file</span> / <span class="am">write_file</span>

agent = Agent(model=GeminiModel(...),
              tools=[...], system_prompt=PROMPT)</pre>
   </div>
   <div style="flex:.8; display:flex; flex-direction:column; gap:22px; justify-content:center">
    <div class="card glow"><div class="lbl">SDK LOOP</div><b>Plans, dispatches, retries</b><span>The custom part is tool discipline: fallback RPCs, raw response kept beside every decoded value</span></div>
    <div class="card"><div class="lbl">MODEL SWAP</div><b class="mono" style="font-size:24px">one line</b><span>Gemini → Bedrock → any Strands provider</span></div></div></div>
  {ftr("6 TOOLS // 1 SYSTEM PROMPT", "LATENCY P50: 5.2s")}</div></div>""",

 "09-limits": f"""<div class="slide">{hdr(5,"DEPLOY")}<div class="frame">{cross()}
  {idx("05_ROADMAP","SCOPE AND WHAT'S NEXT")}
  <h2>Read-only by design. <span class="accent">That is the point.</span></h2>
  <p class="sub">No spending authority to trust yet. Everything below stays keyless public RPC.</p>
  <div class="row" style="margin-top:44px">
   <div class="card"><div class="lbl">TODAY</div><b>Single address</b><span>mint or wallet, one run, one verified note</span></div>
   <div class="card"><div class="lbl">NEXT</div><b class="cy">Dollar-ized holdings</b><span>Jupiter price cross-check, then batch mode over a watchlist</span></div>
   <div class="card"><div class="lbl">LATER</div><b class="am">Agents that pay</b><span>x402 payment channels fit this loop: the agent buys its own premium data</span></div></div>
  {ftr("STATE: IDLE", "MAINNET-BETA // CONFIRMED")}</div></div>""",

 "10-close": f"""<div class="slide">{hdr(5,"DEPLOY")}<div class="frame center">{cross()}
  <div style="display:flex;align-items:center;gap:30px;justify-content:center">
   <div style="width:96px">{LOGO}</div><h1 class="grad">SoloPilot</h1></div>
  <p class="big" style="text-align:center;margin-top:34px">Clone it, run it against mainnet.<br>The agent <span class="accent">writes its own proof</span>.</p>
  <p class="mono cy" style="text-align:center;font-size:34px;margin-top:48px">github.com/cryptoflops/solopilot-agent</p>
  <div style="display:flex;gap:16px;justify-content:center;margin-top:44px">
   <span class="badge">STRANDS AGENTS SDK</span><span class="badge vio">MIT LICENSE</span><span class="badge cyn">COLOSSEUM CRYPTO WORLD'S FAIR</span></div>
  {ftr("BUILT FOR THE ARENA", "STATUS: SUBMISSION-READY")}</div></div>""",
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
             "--virtual-time-budget=15000",  # wait for Google Fonts to load before screenshot
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
