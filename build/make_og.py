"""링크 미리보기(Open Graph·Twitter) 이미지: 언어별 홈 첫 화면을 1200×630으로 찍어 docs/assets/og-<lang>.png로 저장한다.
make_site.py·make_pages.py가 og:image로 이 파일을 가리킨다. Playwright가 없으면 건너뛴다(이미 커밋된 이미지를 그대로 쓴다).
사용: make_og.py <docs 폴더>"""
import asyncio, os, sys
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[og 이미지] playwright 없음 — 건너뜀"); sys.exit(0)
docs = os.path.abspath(sys.argv[1])
PAGES = {"en": "index.html", "ko": "ko/index.html", "ja": "ja/index.html", "zh": "zh/index.html"}

async def run():
    async with async_playwright() as p:
        exe = "/opt/pw-browsers/chromium"
        b = await p.chromium.launch(**({"executable_path": exe} if os.path.exists(exe) else {}))
        ctx = await b.new_context(viewport={"width": 1200, "height": 630}, color_scheme="light", reduced_motion="reduce")
        pg = await ctx.new_page()
        await pg.add_init_script("try{localStorage.setItem('vla-theme','light')}catch(e){}")
        for l, f in PAGES.items():
            await pg.goto("file://" + os.path.join(docs, f))
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(800)
            out = os.path.join(docs, "assets", "og-%s.png" % l)
            await pg.screenshot(path=out)
            print(out, os.path.getsize(out), "bytes")
        await b.close()
asyncio.run(run())
