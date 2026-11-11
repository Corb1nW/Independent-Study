"""Browser check of a muscle viewer page: every mode shows its own data (ChatGPT finding D3-B02).

    python -m tools.check_viewer results/phase_d/<viewer>.html [--screenshots DIR]

Opens the page in headless Chromium (Playwright with a system Chrome or Playwright's own Chromium), then for
each knee mode and body checks that the visible assumptions, badges, feasibility panel and footer all come
from the same manifest as the run being shown, that a moving-knee view never states the fixed knee or
fixed-knee torques as an assumption, and that the page has no script errors and no horizontal scroll at
desktop and phone widths. Exit code 1 on any problem. Needs a browser, so it is not part of the test suite.
"""
import argparse
import asyncio
import shutil
import sys
from pathlib import Path

FIXED_ONLY_PHRASES = ("fixed-centre knee", "inertial torques are kept")


async def check(path, shots):
    from playwright.async_api import async_playwright
    problems, report = [], []
    async with async_playwright() as p:
        chrome = shutil.which("google-chrome") or shutil.which("chromium")
        browser = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else \
            await p.chromium.launch()
        for width, height, scheme in ((1280, 1900, "light"), (390, 2800, "dark")):
            page = await browser.new_page(viewport={"width": width, "height": height}, color_scheme=scheme)
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.goto(Path(path).resolve().as_uri())
            await page.wait_for_timeout(500)
            has_moving = await page.evaluate("Boolean(DATA.moving)")
            modes = [("moving", 1), ("fixed", 2)] if has_moving else [("fixed", None)]
            bodies = await page.evaluate("DATA.runs.map(r => r.body)")
            for mode, button in modes:
                if button:
                    await page.click(f"#knees button:nth-child({button})")
                for b, body in enumerate(bodies, 1):
                    await page.click(f"#bodies button:nth-child({b})")
                    await page.evaluate("i = 150; playing = false; syncPlay(); frame()")
                    got = await page.evaluate("""() => ({
                        knee: V.knee, body: run.body, commit: V.commit,
                        expected_status: run.status.muscle_feasibility,
                        assumptions: [...document.querySelectorAll('#assump li')].map(li => li.textContent),
                        summary: document.getElementById('assump-summary')?.textContent ?? '',
                        expected_count: (V.assumptions || []).length,
                        feas: document.getElementById('feas')?.textContent ?? '',
                        foot: document.getElementById('foot')?.textContent ?? '',
                        badges: document.getElementById('badges')?.textContent ?? '',
                        eyebrow: document.getElementById('eyebrow')?.textContent ?? ''})""")
                    where = f"{width}px {mode} {body}"
                    if got["knee"] != mode or got["body"] != body:
                        problems.append(f"{where}: page shows {got['knee']} {got['body']}")
                    if not got["expected_count"] or len(got["assumptions"]) != got["expected_count"] \
                            or str(got["expected_count"]) not in got["summary"]:
                        problems.append(f"{where}: assumption list does not match the manifest's")
                    if mode == "moving":
                        bad = [a for a in got["assumptions"] for ph in FIXED_ONLY_PHRASES if ph in a]
                        if bad:
                            problems.append(f"{where}: moving-knee view states a fixed-knee assumption: {bad[0][:90]}")
                        if not any("D1's motion" in a and "moving knee" in a for a in got["assumptions"]):
                            problems.append(f"{where}: moving-knee view does not say D1's motion is retained")
                    if has_moving and ("Moving knee:" in got["badges"]) != (mode == "moving"):
                        problems.append(f"{where}: badge names the other knee")
                    if got["commit"][:12] not in got["foot"]:
                        problems.append(f"{where}: footer does not cite the shown run's commit")
                    want = "feasible throughout" if got["expected_status"] == "feasible" else "short of torque"
                    if want not in got["feas"]:
                        problems.append(f"{where}: feasibility panel disagrees with the run's status")
                    if ("D3" in got["eyebrow"]) != (mode == "moving"):
                        problems.append(f"{where}: heading names the other stage")
                    report.append(f"{where}: {len(got['assumptions'])} assumptions, status {got['expected_status']}, "
                                  f"commit {got['commit'][:7]}")
                if shots:
                    Path(shots).mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(Path(shots) / f"viewer_{width}_{mode}.png"), full_page=True)
            scroll = await page.evaluate("document.documentElement.scrollWidth")
            if scroll > width:
                problems.append(f"{width}px: horizontal scroll ({scroll}px)")
            problems += [f"{width}px: script error: {e}" for e in errors]
            await page.close()
        await browser.close()
    return problems, report


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("page", type=Path)
    ap.add_argument("--screenshots")
    args = ap.parse_args()
    problems, report = asyncio.run(check(args.page, args.screenshots))
    for line in report + problems:
        print(line)
    print("VIEWER CHECK", "PASSED" if not problems else f"FAILED ({len(problems)})")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
