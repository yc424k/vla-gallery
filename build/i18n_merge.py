"""i18n/work/<lang>_*.json을 합쳐 i18n/<lang>.json을 만든다. 숫자가 원문과 다른 항목은 경고한다(키·값 어긋남 탐지).
사용: i18n_merge.py <lang> [추가 번역 json ...]"""
import sys, json, glob, re, os
lang = sys.argv[1]
root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "i18n")
out = {}
for f in sorted(glob.glob(os.path.join(root, "work", lang + "_*.json"))) + sys.argv[2:]:
    if ".part" in f: continue
    out.update(json.load(open(f, encoding="utf-8")))
NUM = re.compile(r'\d+(?:[.,]\d+)?')
def nums(t): return {n for n in NUM.findall(t.replace(",", "")) if n not in ("1", "2")}
# 원문에 숫자가 2개 이상인데 번역문에 하나도 없으면 다른 문장의 번역이 붙은 것으로 본다
odd = [k for k, v in out.items() if len(nums(k)) >= 2 and not (nums(k) & nums(v))]
json.dump(dict(sorted(out.items())), open(os.path.join(root, lang + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(lang, len(out), "entries; misaligned", len(odd))
for k in odd[:15]: print("   ", k[:70], "=>", out[k][:70])
