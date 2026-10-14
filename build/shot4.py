import sys, asyncio, json
from playwright.async_api import async_playwright
outdir = sys.argv[1]
page_html = open(outdir + "/../gallery/vla-gallery.html", encoding="utf-8").read()
skel = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>'
        '</head><body>' + page_html + '</body></html>')
open(outdir + "/wrapped.html", "w", encoding="utf-8").write(skel)
async def el_shot(pg, sel, path, h=None):
    box = await pg.evaluate(f"(()=>{{const e=document.querySelector('{sel}');const r=e.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,r.height]}})()")
    await pg.screenshot(path=path, full_page=True, clip={"x": max(box[0]-4,0), "y": box[1]-4, "width": box[2]+8, "height": (h or box[3])+8})
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, scheme in [("desk-light", 1280, "light"), ("desk-dark", 1280, "dark"), ("phone-dark", 400, "dark")]:
            ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme)
            pg = await ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errs.append("console." + m.type + ": " + m.text) if m.type == "error" and "fonts.g" not in m.text and "ERR_" not in m.text else None)
            await pg.goto("file://" + outdir + "/wrapped.html"); await pg.wait_for_timeout(1500)
            print(name, "scrollWidth", await pg.evaluate("document.documentElement.scrollWidth"), errs)
            await el_shot(pg, "#base", f"{outdir}/{name}-base.png")
            if name == "desk-light":
                print("stats:", (await pg.evaluate("document.getElementById('stats').innerText")).replace("\n", " | "))
                for t in ["base-lead", "rl-lead", "tier-lead", "infer-lead", "llm-lead"]:
                    print(t, ":", await pg.evaluate(f"document.getElementById('{t}').textContent"))
                await el_shot(pg, "#mem-chart", f"{outdir}/{name}-memchart.png")
                await el_shot(pg, "#rl-chart", f"{outdir}/{name}-rlchart.png")
                await el_shot(pg, "#fam-chart", f"{outdir}/{name}-famchart.png")
                await el_shot(pg, ".hero", f"{outdir}/{name}-hero.png")
                for cid in ["navila", "nomad", "pi0-5", "quar-vla", "abot-n0", "gnm", "tidybot"]:
                    await el_shot(pg, f"#m-{cid}", f"{outdir}/{name}-card-{cid}.png", 900)
                res = await pg.evaluate("""(()=>{
                  const out={}; const sel=document.getElementById('f-base');
                  out.opts=[...sel.options].map(o=>o.text);
                  for (const o of [...sel.options]){ if(!o.value) continue; sel.value=o.value; sel.dispatchEvent(new Event('change')); out[o.text]=document.getElementById('f-count').textContent; }
                  sel.value=''; sel.dispatchEvent(new Event('change'));
                  const g=[...document.querySelectorAll('#f-groups .chip')].map(c=>c.textContent); out.groups=g;
                  const q=document.getElementById('f-q');
                  for (const t of ['웨이포인트','Walk These Ways','Jetson Orin NX','Go2']){ q.value=t; q.dispatchEvent(new Event('input')); out['q:'+t]=document.getElementById('f-count').textContent; }
                  q.value=''; q.dispatchEvent(new Event('input'));
                  out.cards=document.querySelectorAll('#grid .card').length;
                  out.baseRows=document.querySelectorAll('#base-matrix tbody tr').length;
                  out.tierRows=document.querySelectorAll('#tier-table tbody tr').length;
                  out.badChipLinks=[...document.querySelectorAll('#base-matrix a.mchip')].filter(a=>!document.getElementById(a.getAttribute('href').slice(1))).length;
                  return out; })()""")
                print(json.dumps(res, ensure_ascii=False, indent=1))
                await pg.select_option("#cmp-a", "navila"); await pg.select_option("#cmp-b", "pi0-5"); await pg.wait_for_timeout(200)
                row = await pg.evaluate("[...document.querySelectorAll('#cmp-table tr')].find(r=>r.querySelector('th')&&r.querySelector('th').textContent==='베이스 제어').innerText")
                print("compare base row:", row.replace("\n", " | "))
                await pg.click("#v-compact"); await pg.wait_for_timeout(300)
                await el_shot(pg, "#compact", f"{outdir}/{name}-compact.png", 500)
                await pg.click("#v-detail")
            if name == "phone-dark":
                await el_shot(pg, "#m-navila", f"{outdir}/{name}-card-navila.png", 1100)
            await ctx.close()
        await b.close()
asyncio.run(run())
