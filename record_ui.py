"""Record the live SoloPilot console: USDC mint triage, then wallet triage.
Emits webm + timings.json for the mux step. Server must be up on :8000."""
import asyncio, json, time, os, shutil
from playwright.async_api import async_playwright

OUT = "/tmp/sp-rec"; shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

async def run_preset(page, addr, cap=180):
    await page.click(f'.pbtn[data-addr="{addr}"]')
    await page.wait_for_timeout(700)
    await page.locator("#run-btn").click()
    t0 = time.time()
    try:
        await page.wait_for_selector(".verify.show", timeout=cap * 1000)
    except Exception:
        pass
    return time.time() - t0

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900},
                                  record_video_dir=OUT,
                                  record_video_size={"width": 1440, "height": 900})
        page = await ctx.new_page()
        t = {}
        await page.goto("http://127.0.0.1:8000/")
        t["load"] = time.time()
        await page.wait_for_timeout(1800)

        # shot 1: USDC mint (the hero: symbol+supply+authorities decode)
        t["usdc_s"] = time.time()
        d1 = await run_preset(page, "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        t["usdc_e"] = time.time()
        await page.evaluate("document.getElementById('dossier').scrollIntoView()")
        await page.wait_for_timeout(4000)

        # shot 2: reset, then the USDC mint-authority wallet (holdings story)
        await page.click("#reset-btn")
        await page.wait_for_timeout(800)
        t["auth_s"] = time.time()
        d2 = await run_preset(
            page, "BJE5MMbqXjVwjAF7oxwPYXnTXDyspzZyt4vwenNw5ruG")
        t["auth_e"] = time.time()
        await page.evaluate("document.getElementById('dossier').scrollIntoView()")
        await page.wait_for_timeout(4000)

        await ctx.close()
        vid = os.path.join(OUT, "video.webm")
        vp = await page.video.path() if page.video else None
        if vp and os.path.exists(vp):
            shutil.move(vp, vid)
        json.dump({"usdc_run_s": d1, "auth_run_s": d2,
                   **{k: v - t["load"] for k, v in t.items()}},
                  open(f"{OUT}/timings.json", "w"), indent=1)
        print("RECORDED", vid, os.path.getsize(vid) if os.path.exists(vid) else "MISSING")

asyncio.run(main())
