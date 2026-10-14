"""gallery/vla-gallery.html(아티팩트용 본문)을 GitHub Pages 등에 바로 올릴 수 있는 완전한 HTML 문서로 감싼다.
검색 노출용 메타 태그(canonical·hreflang·Open Graph·JSON-LD)를 넣고, 한국어(사이트 맨 위) 빌드 때 robots.txt와 sitemap.xml을 만든다.
사용: make_site.py <본문 html> <출력 html> [lang]   (lang: ko(기본)·en·ja·zh)"""
import datetime, html as H, json, os, sys
src, out = sys.argv[1:3]
lang = sys.argv[3] if len(sys.argv) > 3 else "ko"
SITE = "https://vla-gallery.is-a.dev/"
LANGS = ["ko", "en", "ja", "zh"]
LOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}
url_of = lambda l: SITE if l == "ko" else SITE + l + "/"
URL = url_of(lang)
s = open(src, encoding="utf-8").read()
# 본문 시작: 첫 화면 위 진행 막대·메뉴가 있으면 거기서, 없으면 히어로에서 자른다
i = min(s.index(x) for x in ('<div class="progress"', '<header class="hero">') if x in s)
head, body = s[:i], s[i:]

def meta(attr, key, val):
    return '<meta %s="%s" content="%s">\n' % (attr, key, H.escape(val, quote=True))

title = s[s.index("<title>") + 7:s.index("</title>")]
desc_at = s.index('<meta name="description" content="') + 34
desc = H.unescape(s[desc_at:s.index('"', desc_at)])
today = datetime.date.today().isoformat()
KW_KO = ["VLA", "Vision-Language-Action", "로봇 파운데이션 모델", "robot foundation model",
         "로봇 매니퓰레이션", "휴머노이드", "모바일 매니퓰레이션", "로봇 내비게이션",
         "액션 헤드", "flow matching", "diffusion policy", "추론 메모리"]
KW_EN = ["VLA", "Vision-Language-Action", "robot foundation model", "robot manipulation", "humanoid",
         "mobile manipulation", "robot navigation", "action head", "flow matching", "diffusion policy", "inference memory"]
ld = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "name": title, "alternateName": "VLA Gallery", "url": URL, "inLanguage": lang},
        {"@type": "Dataset", "name": "로봇 VA·VLA 모델 비교표 (Robot Vision-Language-Action model comparison)" if lang == "ko" else title,
         "description": desc, "url": URL, "inLanguage": lang, "dateModified": today,
         "temporalCoverage": "2022/2026", "isAccessibleForFree": True,
         "keywords": KW_KO if lang == "ko" else KW_EN},
    ],
}
alts = "".join('<link rel="alternate" hreflang="%s" href="%s">\n' % ("zh-Hans" if l == "zh" else l, url_of(l)) for l in LANGS)
alts += '<link rel="alternate" hreflang="x-default" href="%s">\n' % SITE
seo = ("<link rel=\"canonical\" href=\"%s\">\n" % URL + alts
       + meta("name", "google-site-verification", "Sdh4f6GJQFA6JrVspVS-Lcn_mAKMHdw-4H8wNxJZg2A")
       + meta("name", "robots", "index, follow, max-image-preview:large")
       + meta("name", "keywords", ", ".join(KW_KO + ["OpenVLA", "pi0", "GR00T", "RT-2"]) if lang == "ko" else ", ".join(KW_EN + ["OpenVLA", "pi0", "GR00T", "RT-2"]))
       + meta("property", "og:type", "website") + meta("property", "og:site_name", "VLA Gallery")
       + meta("property", "og:title", title) + meta("property", "og:description", desc)
       + meta("property", "og:url", URL) + meta("property", "og:locale", LOCALE[lang])
       + "".join(meta("property", "og:locale:alternate", LOCALE[l]) for l in LANGS if l != lang)
       + meta("name", "twitter:card", "summary") + meta("name", "twitter:title", title)
       + meta("name", "twitter:description", desc)
       + '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>\n")
head = head.replace("</title>\n", "</title>\n" + seo, 1)

html = ('<!doctype html>\n<html lang="' + lang + '">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}[hidden]{display:none!important}</style>\n' + head + '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(out, "w", encoding="utf-8").write(html)
print(out, len(html.encode("utf-8")), "bytes")

if lang == "ko":
    d = os.path.dirname(out) or "."
    open(os.path.join(d, "robots.txt"), "w", encoding="utf-8").write("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % SITE)
    links = "".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>\n' % ("zh-Hans" if l == "zh" else l, url_of(l)) for l in LANGS)
    open(os.path.join(d, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join("  <url><loc>%s</loc><lastmod>%s</lastmod>\n%s  </url>\n" % (url_of(l), today, links) for l in LANGS)
        + "</urlset>\n")
