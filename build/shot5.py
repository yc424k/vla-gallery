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
    await pg.screenshot(path=path, full_page=True, clip={"x": max(box[0]-4,0), "y": box[1]-4, "width": box[2]+8, "height": min(h or box[3], 2600)+8})
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
            await el_shot(pg, "#fit", f"{outdir}/{name}-fit.png", 1500)
            if name == "desk-light":
                res = await pg.evaluate("""(()=>{
                  const out={}; const dev=document.getElementById('fit-dev'), pr=document.getElementById('fit-prec'), hz=document.getElementById('fit-hz');
                  const snap=()=>[...document.querySelectorAll('#fit-sum .k')].map(k=>k.textContent).join('/');
                  for (const [d,p,h] of [['rtx-4090','2','5'],['rtx-4090','0.5','5'],['jetson-orin-nx-16','0.5','2'],['jetson-agx-thor','2','5'],['rtx-3060-12','2','5'],['h100-sxm','2','10'],['rtx-4060-laptop','0.5','1']]){
                    dev.value=d; pr.value=p; hz.value=h; dev.dispatchEvent(new Event('change'));
                    const top=[...document.querySelectorAll('#fit-table tbody tr:not(.grp)')].slice(0,6).map(r=>r.cells[0].textContent+' '+r.cells[2].textContent+' '+r.cells[7].textContent.slice(0,40));
                    out[d+'/'+p+'/'+h]={counts:snap(), top};
                  }
                  dev.value='rtx-4090'; pr.value='2'; hz.value='5'; dev.dispatchEvent(new Event('change'));
                  document.getElementById('fit-go').click();
                  out.gallery=document.getElementById('f-count').textContent;
                  out.fitlines=[...document.querySelectorAll('.fitline')].filter(e=>e.textContent.trim()).length;
                  out.openvla=document.querySelector('[data-fit="openvla"]').textContent;
                  out.pi0=document.querySelector('[data-fit="pi0"]').textContent;
                  out.helix=document.querySelector('[data-fit="figure-helix"]').textContent;
                  out.gnm=document.querySelector('[data-fit="gnm"]').textContent;
                  document.getElementById('f-reset').click(); out.reset=document.getElementById('f-count').textContent;
                  dev.value='custom'; dev.dispatchEvent(new Event('change')); out.customHidden=document.getElementById('fit-custom').hidden; out.custom=snap();
                  dev.value='rtx-4090'; dev.dispatchEvent(new Event('change'));
                  return out; })()""")
                print(json.dumps(res, ensure_ascii=False, indent=1))
                await el_shot(pg, "#m-openvla", f"{outdir}/{name}-card-openvla.png", 1100)
            await ctx.close()
        await b.close()
asyncio.run(run())
