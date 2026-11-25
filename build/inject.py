"""template.html에 데이터·장치·번역을 넣어 페이지 본문을 만든다.
사용: inject.py <template> <data.json> <out> [lang]   (lang: ko(기본)·en·ja·zh, 번역은 i18n/<lang>.json)"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_html import translate
tpl, data, out = sys.argv[1:4]
lang = sys.argv[4] if len(sys.argv) > 4 else "ko"
s = open(tpl, encoding="utf-8").read()
d = json.load(open(data, encoding="utf-8"))
dev_path = os.path.join(os.path.dirname(os.path.abspath(data)), "devices.json")
if "__DEVICES__" in s:
    dv = json.load(open(dev_path, encoding="utf-8"))
    assert s.count("__DEVICES__") == 1
    s = s.replace("__DEVICES__", json.dumps(dv, ensure_ascii=False).replace("</", "<\\/"))
tr = {}
if lang != "ko":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "i18n")
    tr = json.load(open(os.path.join(root, lang + ".json"), encoding="utf-8"))
    s = translate(s, tr)
assert s.count("__LANG__") == 1 and s.count("__I18N__") == 1
s = s.replace("__LANG__", lang).replace("__I18N__", json.dumps(tr, ensure_ascii=False).replace("</", "<\\/"))
# 홈의 모델별 사양 페이지 목록: JS 없이도 검색엔진이 모델 페이지(m/<id>/)를 따라가게 정적 링크로 넣는다
import html as H
groups = []
for m in sorted(d, key=lambda m: m["gi"]):
    if m["group"] not in [g for g, _ in groups]: groups.append((m["group"], []))
    groups[[g for g, _ in groups].index(m["group"])][1].append(m)
links = "".join('<div><dt>%s<span>%d</span></dt><dd>%s</dd></div>' % (H.escape(tr.get(g, g)), len(ms),
                '\n'.join('<a href="m/%s/">%s</a>' % (m["id"], H.escape(tr.get(m["name"], m["name"]))) for m in ms)) for g, ms in groups)
assert s.count("__MODEL_LINKS__") == 1
s = s.replace("__MODEL_LINKS__", links)
js = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
assert s.count("__DATA__") == 1
s = s.replace("__DATA__", js)
open(out, "w", encoding="utf-8").write(s)
print(out, lang, len(s.encode("utf-8")), "bytes")
