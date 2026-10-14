"""번역할 한국어 문자열을 모두 모은다: 페이지 문구(HTML·T(...))와 데이터 값.
출력: i18n/source.json  {"ui": [...], "data": [...]}"""
import sys, os, re, json, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jslit import literals, KO
tpl, data, devs, out = sys.argv[1:5]
s = open(tpl, encoding="utf-8").read()

from i18n_html import segments as html_segments

ui = html_segments(s)
a = s.index('<script id="vla-data"'); a = s.index("<script>", a) + len("<script>"); b = s.index("</script>", a)
js = s[a:b]
for (i, j, q) in literals(js):
    if js[:i].rstrip().endswith("T(") and KO.search(js[i:j]):
        ui.append(ast.literal_eval(js[i:j]))

def short(name):
    m = re.match(r'^(.*?) \((.+?)\)(.*)$', name)
    return (m.group(1) + m.group(3)).strip() if m and len(m.group(2)) > 13 else name
vals = []
def walk(v):
    if isinstance(v, str): vals.append(v)
    elif isinstance(v, list): [walk(x) for x in v]
    elif isinstance(v, dict): [walk(x) for x in v.values()]
D = json.load(open(data, encoding="utf-8"))
for m in D:
    walk(m)
    llm = m.get("llm") or ""
    if " · " in llm: vals += [llm.split(" · ")[0], " · ".join(llm.split(" · ")[1:])]
    pr = m.get("params") or ""
    vals += [re.split(r'[;(]', pr)[0].strip(), pr.split(";")[0]]
    gb = m.get("gpuh_basis") or ""
    vals.append(re.split(r'[(;]', "·".join(gb.split("·")[1:]))[0].strip())
    vals += [short(m["name"]), re.sub(r' \(.*\)$', "", m["name"])]
for d in json.load(open(devs, encoding="utf-8")):
    walk({k: v for k, v in d.items() if k != "src"})
data_keys = sorted({v for v in vals if KO.search(v)})
KEEP = {"한국어"}  # 언어 선택의 언어 이름은 번역하지 않는다
ui_keys = []
for u in ui:
    if u not in ui_keys and u not in data_keys and u not in KEEP: ui_keys.append(u)
json.dump({"ui": ui_keys, "data": data_keys}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ui", len(ui_keys), sum(map(len, ui_keys)), "chars | data", len(data_keys), sum(map(len, data_keys)), "chars")
