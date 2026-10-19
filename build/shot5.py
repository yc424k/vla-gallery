import sys, asyncio, json
from playwright.async_api import async_playwright
outdir = sys.argv[1]
page_html = open(outdir + "/../gallery/vla-gallery.html", encoding="utf-8").read()
skel = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
        '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>'
        '</head><body>' + page_html + '</body></html>')
open(outdir + "/wrapped.html", "w", encoding="utf-8").write(skel)
async def el_shot(pg, sel, path, h=None):
    # 섹션마다 페이지가 나뉘어 있으므로 그 요소가 든 페이지로 먼저 옮긴다
    await pg.evaluate(f"(()=>{{const e=document.querySelector('{sel}');const s=e.closest('main>section,footer');const h=s?s.id:'';if(location.hash.slice(1)!==h)location.hash=h;}})()")
    await pg.wait_for_timeout(300)
    box = await pg.evaluate(f"(()=>{{const e=document.querySelector('{sel}');const r=e.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,r.height]}})()")
    await pg.screenshot(path=path, full_page=True, clip={"x": max(box[0]-4,0), "y": box[1]-4, "width": box[2]+8, "height": min(h or box[3], 2600)+8})
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, scheme in [("desk-light", 1280, "light"), ("desk-dark", 1280, "dark"), ("phone-dark", 400, "dark")]:
            # 모션을 끄고 찍는다(스크롤 등장 애니메이션 때문에 화면 밖 섹션이 비어 보이지 않게)
            ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme, reduced_motion="reduce")
            pg = await ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errs.append("console." + m.type + ": " + m.text) if m.type == "error" and "fonts.g" not in m.text and "ERR_" not in m.text else None)
            await pg.goto("file://" + outdir + "/wrapped.html"); await pg.wait_for_timeout(1500)
            print(name, "scrollWidth", await pg.evaluate("document.documentElement.scrollWidth"), errs)
            await el_shot(pg, "#fit", f"{outdir}/{name}-fit.png", 1500)
            await el_shot(pg, "#tune", f"{outdir}/{name}-tune.png", 1800)
            print(name, "tune scrollWidth", await pg.evaluate("document.documentElement.scrollWidth"))
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
                tune = await pg.evaluate("""(()=>{
                  const out={}, f=id=>document.getElementById(id);
                  const snap=()=>[...document.querySelectorAll('#tune-sum .k')].map(k=>k.textContent).join('/');
                  for (const [d,n,m,bs] of [['rtx-4090','1','lora','n'],['rtx-4090','1','lora','s'],['rtx-4090','1','full','n'],['rtx-4090','1','qlora','s'],['rtx-4090','1','head','n'],['a100-80','8','full','n'],['jetson-agx-thor','4','lora','n']]){
                    f('tune-dev').value=d; f('tune-n').value=n; f('tune-m').value=m; f('tune-bs').value=bs; f('tune-dev').dispatchEvent(new Event('change'));
                    const top=[...document.querySelectorAll('#tune-table tbody tr:not(.grp)')].slice(0,4).map(r=>r.cells[0].textContent+' '+r.cells[2].textContent+' '+r.cells[3].textContent);
                    out[[d,n,m,bs].join('/')]={counts:snap(), n:f('tune-n').value, top};
                  }
                  f('tune-dev').value='rtx-4090'; f('tune-n').value='1'; f('tune-m').value='lora'; f('tune-bs').value='n'; f('tune-dev').dispatchEvent(new Event('change'));
                  return out; })()""")
                print(json.dumps(tune, ensure_ascii=False, indent=1))
                await el_shot(pg, "#m-openvla", f"{outdir}/{name}-card-openvla.png", 1100)
            await ctx.close()
        await b.close()
asyncio.run(run())
