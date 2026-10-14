"""번역 파일 점검: 빠진 키, 한글 남음, {0} 자리표시 불일치, 앞뒤 공백 불일치.
사용: python3 build/i18n_check.py <원문 목록 json(list)> <번역 json(dict)> [--fix-space]"""
import sys, json, re
src = json.load(open(sys.argv[1], encoding="utf-8")); tr = json.load(open(sys.argv[2], encoding="utf-8"))
if isinstance(src, dict): src = src["ui"] + src["data"]
KO = re.compile(r'[가-힣]'); PH = re.compile(r'\{\d+\}')
bad = {"missing": [], "hangul": [], "placeholder": [], "space": [], "wrong_language": []}
import os
LANG = os.path.basename(sys.argv[2])[:2]
KANA = re.compile(r'[\u3040-\u30ff]'); CJK = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
def wrong(k, v):
    if LANG == "en": return bool(CJK.search(v)) and not CJK.search(k)
    if LANG == "zh": return bool(KANA.search(v))
    if LANG == "ja": return len(k) >= 20 and len(KO.findall(k)) >= 10 and not KANA.search(v)
    return False
fix = "--fix-space" in sys.argv
for k in src:
    if k not in tr: bad["missing"].append(k); continue
    v = tr[k]
    if not isinstance(v, str): bad["missing"].append(k); continue
    if KO.search(v): bad["hangul"].append(k)
    if wrong(k, v): bad["wrong_language"].append(k)
    if sorted(PH.findall(k)) != sorted(PH.findall(v)): bad["placeholder"].append(k)
    lead = k[:len(k) - len(k.lstrip())]; trail = k[len(k.rstrip()):]
    if not (v.startswith(lead) and v.endswith(trail)) or v[:len(v)-len(v.lstrip())] != lead or v[len(v.rstrip()):] != trail:
        if fix: tr[k] = lead + v.strip() + trail
        else: bad["space"].append(k)
if fix: json.dump(tr, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for kind, ks in bad.items():
    print(kind, len(ks))
    for k in ks[:8]: print("   ", repr(k[:100]))
print("OK" if not any(bad.values()) else "FIX NEEDED")
