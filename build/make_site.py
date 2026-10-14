"""gallery/vla-gallery.html(아티팩트용 본문)을 GitHub Pages 등에 바로 올릴 수 있는 완전한 HTML 문서로 감싼다.
검색 노출용 메타 태그(canonical·Open Graph·JSON-LD)를 넣고, 같은 폴더에 robots.txt와 sitemap.xml을 만든다."""
import datetime, html as H, json, os, sys
src, out = sys.argv[1:3]
SITE = "https://vla-gallery.is-a.dev/"
s = open(src, encoding="utf-8").read()
i = s.index('<header class="hero">')
head, body = s[:i], s[i:]

def meta(attr, key, val):
    return '<meta %s="%s" content="%s">\n' % (attr, key, H.escape(val, quote=True))

title = s[s.index("<title>") + 7:s.index("</title>")]
desc_at = s.index('<meta name="description" content="') + 34
desc = H.unescape(s[desc_at:s.index('"', desc_at)])
today = datetime.date.today().isoformat()
ld = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "name": title, "alternateName": "VLA Gallery", "url": SITE, "inLanguage": "ko"},
        {"@type": "Dataset", "name": "로봇 VA·VLA 모델 비교표 (Robot Vision-Language-Action model comparison)",
         "description": desc, "url": SITE, "inLanguage": "ko", "dateModified": today,
         "temporalCoverage": "2022/2026", "isAccessibleForFree": True,
         "keywords": ["VLA", "Vision-Language-Action", "로봇 파운데이션 모델", "robot foundation model",
                      "로봇 매니퓰레이션", "휴머노이드", "모바일 매니퓰레이션", "로봇 내비게이션",
                      "액션 헤드", "flow matching", "diffusion policy", "추론 메모리"]},
    ],
}
seo = ("<link rel=\"canonical\" href=\"%s\">\n" % SITE
       + meta("name", "google-site-verification", "Sdh4f6GJQFA6JrVspVS-Lcn_mAKMHdw-4H8wNxJZg2A")
       + meta("name", "robots", "index, follow, max-image-preview:large")
       + meta("name", "keywords", "VLA, Vision-Language-Action, 로봇 VLA 모델, 로봇 파운데이션 모델, VLA 비교, "
              "OpenVLA, pi0, GR00T, RT-2, 휴머노이드, 모바일 매니퓰레이션, 로봇 내비게이션")
       + meta("property", "og:type", "website") + meta("property", "og:site_name", "VLA Gallery")
       + meta("property", "og:title", title) + meta("property", "og:description", desc)
       + meta("property", "og:url", SITE) + meta("property", "og:locale", "ko_KR")
       + meta("name", "twitter:card", "summary") + meta("name", "twitter:title", title)
       + meta("name", "twitter:description", desc)
       + '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>\n")
head = head.replace("</title>\n", "</title>\n" + seo, 1)

html = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}[hidden]{display:none!important}</style>\n' + head + '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(out, "w", encoding="utf-8").write(html)
print(out, len(html.encode("utf-8")), "bytes")

d = os.path.dirname(out) or "."
open(os.path.join(d, "robots.txt"), "w", encoding="utf-8").write("User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % SITE)
open(os.path.join(d, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    "  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>\n" % (SITE, today))
