"""모델별 정적 페이지와 사이트맵을 만든다(검색 노출용).
사용: make_pages.py <data.json> <i18n 폴더> <docs 폴더>
- 기본 언어(영어) docs/m/<id>/, 다른 언어 docs/<lang>/m/<id>/ (한국어는 원문, 나머지는 i18n/<lang>.json이 있을 때)
- 언어마다 모델 목록 docs[/<lang>]/m/index.html, 공용 스타일 docs/assets/model.css
- docs/sitemap.xml을 홈·모델 목록·모델 페이지 전체로 다시 쓴다
표 항목명과 데이터 값은 갤러리와 같은 번역 사전(i18n/<lang>.json)으로 바꾸고, 이 페이지에만 쓰는 문구는 아래 PL에 있다."""
import datetime, html as H, json, os, re, shutil, sys

data_path, i18n_dir, docs = sys.argv[1:4]
SITE = "https://vla-gallery.is-a.dev/"
DEFAULT = "en"  # 사이트 맨 위(/)에 놓는 언어. make_site.py의 DEFAULT와 같게 둔다
LANGS = [l for l in ("en", "ko", "ja", "zh") if l == "ko" or os.path.exists(os.path.join(i18n_dir, l + ".json"))]
LANGNAME = {"ko": "한국어", "en": "English", "ja": "日本語", "zh": "简体中文"}
HREFLANG = {"ko": "ko", "en": "en", "ja": "ja", "zh": "zh-Hans"}
LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}
today = datetime.date.today().isoformat()
D = json.load(open(data_path, encoding="utf-8"))
TPL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gallery", "template.html"), encoding="utf-8").read()

# 이 페이지에만 쓰는 문구 (ko, en, ja, zh)
PL = {
    "suffix": ("구조·백본 LLM·학습·추론 메모리", "Architecture, Backbone LLM, Training & Inference Memory",
               "構造・バックボーンLLM・学習・推論メモリ", "架构、骨干LLM、训练与推理内存"),
    "home": ("VLA 갤러리", "VLA Gallery", "VLA ギャラリー", "VLA 图库"),
    "list": ("모델 목록", "All models", "モデル一覧", "模型列表"),
    "view": ("갤러리에서 구조도 보기", "View architecture diagram in the gallery", "ギャラリーで構造図を見る", "在图库中查看架构图"),
    "same": ("같은 분류의 모델", "Other models in this category", "同じ分類のモデル", "同类其他模型"),
    "prev": ("이전 모델", "Previous", "前のモデル", "上一个"),
    "next": ("다음 모델", "Next", "次のモデル", "下一个"),
    "s_over": ("개요", "Overview", "概要", "概述"),
    "s_arch": ("구조", "Architecture", "構造", "架构"),
    "s_train": ("학습", "Training", "学習", "训练"),
    "s_inf": ("추론", "Inference", "推論", "推理"),
    "s_rl": ("강화학습 · 베이스", "Reinforcement learning & base", "強化学習・ベース", "强化学习与底盘"),
    "s_note": ("비고", "Notes", "備考", "备注"),
    "list_title": ("로봇 VA·VLA 모델 {0}개 목록", "{0} Robot VA/VLA Models", "ロボット VA・VLA モデル {0} 件一覧", "{0} 个机器人 VA/VLA 模型列表"),
    "list_desc": ("2022~2026 로봇 VA·VLA 모델 {0}개의 개별 사양 페이지. 백본 LLM, 액션 헤드, 학습 GPU·데이터, 추론 장치·메모리, 강화학습, 베이스 제어를 모델마다 정리했다.",
                  "Spec pages for {0} robot VA/VLA models (2022–2026): backbone LLM, action head, training GPUs and data, inference device and memory, RL usage and base control.",
                  "2022〜2026年のロボット VA・VLA モデル {0} 件の個別仕様ページ。バックボーンLLM、アクションヘッド、学習GPU・データ、推論デバイス・メモリ、強化学習、ベース制御をまとめた。",
                  "2022–2026 年 {0} 个机器人 VA/VLA 模型的规格页面：骨干 LLM、动作头、训练 GPU 与数据、推理设备与内存、强化学习和底盘控制。"),
    "count": ("모델 {0}개", "{0} models", "{0} モデル", "{0} 个模型"),
}
LI = {l: i for i, l in enumerate(["ko", "en", "ja", "zh"])}

def font_link():
    m = re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">', TPL)
    return m.group(0) if m else ""

def tokens():
    a = TPL.index(":root{")
    b = TPL.index("*{box-sizing:border-box}")
    return TPL[a:b]

CSS = tokens() + """*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 var(--font-body);-webkit-text-size-adjust:100%}
a{color:var(--accent)}
.wrap{max-width:920px;margin:0 auto;padding:0 16px}
.top{border-bottom:1px solid var(--line);background:var(--surface)}
.top .wrap{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;min-height:48px;font-size:13.5px}
.top a{color:var(--ink-2);text-decoration:none}.top a:hover{color:var(--ink);text-decoration:underline}
.top .brand{font-family:var(--font-display);font-weight:700;color:var(--ink);font-size:15px}
.top .langs{margin-left:auto;display:flex;gap:10px}.top .langs [aria-current]{color:var(--ink);font-weight:600}
.crumb{font-size:13px;color:var(--ink-3);margin:22px 0 0}.crumb a{color:var(--ink-3)}
h1{font-family:var(--font-display);font-size:clamp(26px,5vw,38px);line-height:1.2;margin:8px 0 4px;overflow-wrap:anywhere}
.full{color:var(--ink-2);margin:0 0 4px;font-size:14px}
.by{color:var(--ink-2);margin:0;font-size:14px}
.kv{font-size:13px;color:var(--ink-2);margin:10px 0 0;padding:8px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:4px 18px}
.sum{font-size:16.5px;margin:18px 0}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px}
.acts a{display:inline-block;border:1px solid var(--line);padding:6px 12px;font-size:13.5px;text-decoration:none;color:var(--ink);background:var(--surface)}
.acts a:hover{border-color:var(--ink-3)}
.acts a.pri{background:var(--ink);color:var(--bg);border-color:var(--ink)}
h2{font-family:var(--font-display);font-size:19px;margin:30px 0 6px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
dl{display:grid;grid-template-columns:minmax(0,190px) minmax(0,1fr);margin:0}
dt,dd{padding:8px 0;border-bottom:1px solid var(--line);margin:0;overflow-wrap:anywhere}
dt{color:var(--ink-2);font-size:13.5px;padding-right:14px}
dd{font-size:14.5px}
.paper{font-size:15px}.paper small{font-family:var(--font-data);color:var(--ink-3);margin-left:6px}
.rel ul{list-style:none;padding:0;margin:0;columns:2 220px;column-gap:24px}
.rel li{padding:5px 0;border-bottom:1px solid var(--line);break-inside:avoid;font-size:14px}
.rel li small{color:var(--ink-3);font-family:var(--font-data);margin-left:6px}
.pn{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:34px 0 0}
.pn a{border-top:2px solid var(--ink);padding:8px 0;text-decoration:none;color:var(--ink)}
.pn small{display:block;color:var(--ink-3);font-size:12px}.pn .nx{text-align:right;grid-column:2}
.grp h2 small{font-family:var(--font-data);font-weight:400;color:var(--ink-3);font-size:12.5px;margin-left:8px}
.grp table{width:100%;border-collapse:collapse;font-size:14px}
.grp td{padding:7px 8px 7px 0;border-bottom:1px solid var(--line);vertical-align:top}
.grp td:first-child{width:32%;font-weight:600}.grp td.d{font-family:var(--font-data);font-size:12.5px;color:var(--ink-3);white-space:nowrap;width:70px}
footer{margin:48px 0 0;padding:20px 0 48px;border-top:1px solid var(--line);font-size:13px;color:var(--ink-3)}
@media (max-width:600px){dl{grid-template-columns:1fr}dt{border-bottom:0;padding-bottom:0}.grp td.d{display:none}.grp td:first-child{width:45%}}
"""

HEAD_JS = ('<script>(function(){try{var t=localStorage.getItem("vla-theme");'
           'if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>')

def e(s):
    return H.escape("" if s is None else str(s), quote=True)

def short(name):
    m = re.match(r"^(.*?) \((.+?)\)(.*)$", name)
    return ((m.group(1) + m.group(3)).strip(), name) if m and len(m.group(2)) > 13 else (name, None)

def base_of(l):
    return "/" if l == DEFAULT else "/" + l + "/"

def page_url(l, mid=None):
    return SITE.rstrip("/") + base_of(l) + "m/" + (mid + "/" if mid else "")

def fmt(v, nd=1):
    if v is None: return None
    if isinstance(v, (int, float)):
        return "{:,.0f}".format(v) if nd == 0 else ("{:,.%df}" % nd).format(v).rstrip("0").rstrip(".")
    return str(v)

def clip(s, n=158):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"

def build(l):
    tr = {} if l == "ko" else json.load(open(os.path.join(i18n_dir, l + ".json"), encoding="utf-8"))
    tx = lambda s: s if s is None or s not in tr else tr[s]
    def P(k, *a):
        t = PL[k][LI[l]]
        for i, x in enumerate(a): t = t.replace("{%d}" % i, str(x))
        return t
    NA = tx("미공개")

    def rows(m):
        p = m["paper"]
        base = m["base"]; ts = [t for t in base["types"] if t != "고정"]
        base_t = ("·".join(tx(t) for t in ts) + (" (" + tx(base["cat"]) + ")" if base.get("cat") else "") if ts else tx("고정")) + " · " + tx(base["how"])
        uses = m["rl"] in ("사용", "일부")
        rl_t = tx(m["rl"]) + (" (" + tx(m["rlcat"]) + ")" if uses else "") + " · " + tx(m["rlwhere"])
        gpuh = fmt(m["gpuh"], 0) + " (" + tx(m.get("gpuh_basis") or "") + ")" if m.get("gpuh") is not None else NA
        return [
            ("s_over", [("분류", tx(m["group"])), ("유형", m["type"]), ("발표", m["date"]), ("기관", tx(m["org"])),
                        ("가중치 공개", tx(m["open"])), ("파라미터", tx(m["params"]))]),
            ("s_arch", [("백본 LLM", tx(m["llm"])), ("비전 인코더", tx(m["vis"]) or "—"),
                        ("액션 헤드", tx(m["head"]) + (" (" + tx(m["hk"]) + ")" if m.get("hk") else "")),
                        ("청크", tx(m["chunk"])), ("제어 주기", tx(m["hz"])), ("구조 원문 요약", tx(m["backbone_text"]))]),
            ("s_train", [("사전학습 가속기", tx(m["pre_hw"])), ("사전학습 기간", tx(m["pre_time"])), ("사전학습 스텝·배치", tx(m["pre_steps"])),
                         ("GPU·TPU-시간", gpuh), ("파인튜닝", tx(m["ft"])), ("데이터 종류", tx(m["dtype"])), ("데이터 규모", tx(m["dscale"])),
                         ("주요 데이터셋", tx(m["datasets"])), ("태스크·평가", tx(m["tasks"])), ("로봇", tx(m["robots"]))]),
            ("s_inf", [("추론 장치·속도", tx(m["infer"]) or NA), ("추론 메모리", tx(m["mem"]) or NA),
                       ("가중치 bf16 (계산)", fmt(m["w16"]) + " GB" if m.get("w16") is not None else NA), ("실행 위치", tx(m["dep"]) or NA)]),
            ("s_rl", [("강화학습", rl_t), ("강화학습 근거", m.get("rlsrc")), ("베이스 제어", base_t)]),
            ("s_note", [("핵심 특징", tx(m["feature"])), ("비고", tx(m["note"])), ("검증", tx(m["verify"]))]),
        ]

    def dd(v):
        v = str(v)
        return '<a href="%s" rel="noopener">%s</a>' % (e(v), e(v)) if re.match(r"^https?://\S+$", v) else e(v)

    def head(title, desc, url, alt_urls, ld, kind="article"):
        alts = "".join('<link rel="alternate" hreflang="%s" href="%s">\n' % (HREFLANG[x], alt_urls[x]) for x in LANGS)
        alts += '<link rel="alternate" hreflang="x-default" href="%s">\n' % alt_urls[DEFAULT]
        return ('<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                "<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n"
                '<link rel="canonical" href="%s">\n%s'
                '<meta property="og:type" content="%s"><meta property="og:site_name" content="VLA Gallery">\n'
                '<meta property="og:title" content="%s"><meta property="og:description" content="%s">\n'
                '<meta property="og:url" content="%s"><meta property="og:locale" content="%s">\n'
                '<meta property="og:image" content="%sassets/og-%s.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
                '<meta name="twitter:card" content="summary_large_image">\n'
                '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                "%s\n<link rel=\"stylesheet\" href=\"/assets/model.css\">\n%s\n"
                '<script type="application/ld+json">%s</script>\n</head>\n<body>\n') % (
            l, e(title), e(desc), url, alts, kind, e(title), e(desc), url, LOCALE[l], SITE, l, font_link(), HEAD_JS,
            json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"))

    def top(alt_urls):
        langs = "".join('<a href="%s" hreflang="%s"%s>%s</a>' % (alt_urls[x], HREFLANG[x], ' aria-current="true"' if x == l else "", LANGNAME[x]) for x in LANGS)
        return ('<header class="top"><div class="wrap"><a class="brand" href="%s">%s</a><a href="%sm/">%s</a>'
                '<a href="%s#gallery">%s</a><nav class="langs" aria-label="Language">%s</nav></div></header>\n') % (
            base_of(l), e(P("home")), base_of(l), e(P("list")), base_of(l), e(tx("갤러리")), langs)

    foot = '<footer><div class="wrap">VLA Gallery · <a href="%s">%s</a> · %s</div></footer>\n</body>\n</html>\n' % (
        base_of(l), SITE.replace("https://", "").rstrip("/"), today)

    out_root = os.path.join(docs, "m") if l == DEFAULT else os.path.join(docs, l, "m")
    if os.path.isdir(out_root): shutil.rmtree(out_root)
    groups = []
    for m in D:
        if m["group"] not in groups: groups.append(m["group"])

    for i, m in enumerate(D):
        nm, full = short(m["name"])
        summ = tx(m.get("summary") or m.get("feature") or "")
        title = "%s — %s | VLA Gallery" % (nm, P("suffix"))
        desc = clip("%s (%s, %s) — %s" % (nm, m["org"].split(";")[0].split("·")[0].strip(), m["date"], summ))
        url = page_url(l, m["id"])
        alt_urls = {x: page_url(x, m["id"]) for x in LANGS}
        p = m["paper"]
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "TechArticle", "headline": "%s — %s" % (nm, P("suffix")), "description": desc, "inLanguage": l,
             "url": url, "dateModified": today, "isPartOf": {"@type": "WebSite", "name": "VLA Gallery", "url": SITE},
             "about": {"@type": "SoftwareSourceCode" if m["open"] == "예" else "CreativeWork", "name": m["name"],
                       "creator": {"@type": "Organization", "name": m["org"]}},
             **({"citation": {"@type": "ScholarlyArticle", "name": p["t"], "url": p["u"]}} if p.get("u") else {})},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": P("home"), "item": SITE.rstrip("/") + base_of(l)},
                {"@type": "ListItem", "position": 2, "name": P("list"), "item": page_url(l)},
                {"@type": "ListItem", "position": 3, "name": nm, "item": url}]}]}
        h = [head(title, desc, url, alt_urls, ld), top(alt_urls), '<main class="wrap">\n']
        h.append('<p class="crumb"><a href="%s">%s</a> / <a href="%sm/">%s</a> / %s</p>\n' % (
            base_of(l), e(P("home")), base_of(l), e(P("list")), e(tx(m["group"]))))
        h.append("<h1>%s</h1>\n" % e(nm))
        if full: h.append('<p class="full">%s</p>\n' % e(tx(full)))
        h.append('<p class="by">%s · %s</p>\n' % (e(tx(m["org"])), e(m["date"])))
        kv = [m["type"], tx(m["group"]), tx(m["params"]).split(";")[0].split("(")[0].strip(), tx(m["hk"]) if m.get("hk") else None]
        h.append('<p class="kv">%s</p>\n' % "".join("<span>%s</span>" % e(x) for x in kv if x))
        h.append('<p class="sum">%s</p>\n' % e(summ))
        acts = ['<a class="pri" href="%s#m-%s">%s</a>' % (base_of(l), m["id"], e(P("view")))]
        if p.get("u"): acts.append('<a href="%s" rel="noopener">%s ↗</a>' % (e(p["u"]), e(tx(p["k"]))))
        src = m.get("src")
        if src and src != p.get("u") and "arxiv.org" not in src:
            lab = "GitHub" if "github" in src else "Hugging Face" if "huggingface.co" in src else tx("모델 카드 PDF") if src.lower().endswith(".pdf") else tx("공식 페이지")
            if src not in m["hf"] and not any(src == g or src.startswith(g + "/") for g in m["gh"]): acts.append('<a href="%s" rel="noopener">%s ↗</a>' % (e(src), e(lab)))
        if m["gh"]: acts.append('<a href="%s" rel="noopener">GitHub ↗</a>' % e(m["gh"][0]))
        if m["hf"]: acts.append('<a href="%s" rel="noopener">Hugging Face ↗</a>' % e(m["hf"][0]))
        h.append('<div class="acts">%s</div>\n' % "".join(acts))
        h.append("<h2>%s</h2>\n<p class=\"paper\">" % e(tx("논문")))
        if p.get("u"):
            h.append('<a href="%s" rel="noopener">%s</a><small>%s</small>' % (e(p["u"]), e(p["t"]), e("arXiv " + p["id"] if p.get("id") else tx(p["k"]))))
        else:
            h.append(e(tx("논문 없음")))
            if m.get("prel"):
                r = m["prel"]
                h.append(" · %s<a href=\"%s\" rel=\"noopener\">%s</a>" % (e(tx("관련 ")), e(r["u"]), e(r["t"])))
        h.append("</p>\n")
        if m["gh"]:
            h.append('<h2>GitHub</h2>\n<p class="paper">%s</p>\n' % "<br>".join(
                '<a href="%s" rel="noopener">%s</a>' % (e(u), e(u[19:])) for u in m["gh"]))
        if m["hf"]:
            h.append('<h2>Hugging Face</h2>\n<p class="paper">%s</p>\n' % "<br>".join(
                '<a href="%s" rel="noopener">%s</a>' % (e(u), e(u.split("huggingface.co/")[1])) for u in m["hf"]))
        for sk, rs in rows(m):
            rs = [(k, v) for k, v in rs if v not in (None, "")]
            if not rs: continue
            h.append("<h2>%s</h2>\n<dl>%s</dl>\n" % (e(P(sk)), "".join("<dt>%s</dt><dd>%s</dd>" % (e(tx(k)), dd(v)) for k, v in rs)))
        same = [x for x in D if x["group"] == m["group"] and x["id"] != m["id"]]
        if same:
            h.append('<section class="rel"><h2>%s</h2><ul>%s</ul></section>\n' % (e(P("same")), "".join(
                '<li><a href="%sm/%s/">%s</a><small>%s</small></li>' % (base_of(l), x["id"], e(short(x["name"])[0]), e(x["date"])) for x in same)))
        pn = '<nav class="pn">'
        if i > 0: pn += '<a href="%sm/%s/"><small>← %s</small>%s</a>' % (base_of(l), D[i - 1]["id"], e(P("prev")), e(short(D[i - 1]["name"])[0]))
        if i < len(D) - 1: pn += '<a class="nx" href="%sm/%s/"><small>%s →</small>%s</a>' % (base_of(l), D[i + 1]["id"], e(P("next")), e(short(D[i + 1]["name"])[0]))
        h.append(pn + "</nav>\n</main>\n" + foot)
        d = os.path.join(out_root, m["id"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write("".join(h))

    # 모델 목록
    title = P("list_title", len(D)) + " | VLA Gallery"
    desc = P("list_desc", len(D))
    alt_urls = {x: page_url(x) for x in LANGS}
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": P("list_title", len(D)), "description": desc,
          "url": page_url(l), "inLanguage": l, "dateModified": today,
          "mainEntity": {"@type": "ItemList", "numberOfItems": len(D),
                         "itemListElement": [{"@type": "ListItem", "position": k + 1, "url": page_url(l, m["id"]), "name": short(m["name"])[0]} for k, m in enumerate(D)]}}
    h = [head(title, desc, page_url(l), alt_urls, ld, "website"), top(alt_urls), '<main class="wrap">\n']
    h.append('<p class="crumb"><a href="%s">%s</a> / %s</p>\n<h1>%s</h1>\n<p class="sum">%s</p>\n' % (
        base_of(l), e(P("home")), e(P("list")), e(P("list_title", len(D))), e(desc)))
    for g in groups:
        ms = [m for m in D if m["group"] == g]
        h.append('<section class="grp"><h2>%s<small>%s</small></h2><table>%s</table></section>\n' % (e(tx(g)), e(P("count", len(ms))), "".join(
            '<tr><td><a href="%sm/%s/">%s</a></td><td class="d">%s</td><td>%s</td></tr>' % (
                base_of(l), m["id"], e(short(m["name"])[0]), e(m["date"]), e(clip(tx(m.get("summary") or ""), 90))) for m in ms)))
    h.append("</main>\n" + foot)
    open(os.path.join(out_root, "index.html"), "w", encoding="utf-8").write("".join(h))
    return len(D)

os.makedirs(os.path.join(docs, "assets"), exist_ok=True)
open(os.path.join(docs, "assets", "model.css"), "w", encoding="utf-8").write(CSS)
for l in LANGS:
    print("model pages", l, build(l))

# 사이트맵: 언어별 홈 + 모델 목록 + 모델 페이지
def entry(urls):
    links = "".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % (HREFLANG[x], urls[x]) for x in LANGS)
    links += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n' % urls[DEFAULT]
    return "".join("  <url><loc>%s</loc><lastmod>%s</lastmod>\n%s  </url>\n" % (urls[x], today, links) for x in LANGS)
sets = [{x: SITE.rstrip("/") + base_of(x) for x in LANGS}, {x: page_url(x) for x in LANGS}]
sets += [{x: page_url(x, m["id"]) for x in LANGS} for m in D]
open(os.path.join(docs, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "".join(entry(u) for u in sets) + "</urlset>\n")
print("sitemap", len(sets) * len(LANGS), "urls")
