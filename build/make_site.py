"""gallery/vla-gallery.html(아티팩트용 본문)을 GitHub Pages 등에 바로 올릴 수 있는 완전한 HTML 문서로 감싼다."""
import sys
src, out = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
i = s.index('<header class="hero">')
head, body = s[:i], s[i:]
html = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0}[hidden]{display:none!important}</style>\n' + head + '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(out, "w", encoding="utf-8").write(html)
print(out, len(html.encode("utf-8")), "bytes")
