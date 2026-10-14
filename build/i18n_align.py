"""키와 번역이 어긋난 항목 찾기: 원문의 숫자·영문 단어(모델·장치 이름)가 번역문에 거의 없으면 의심한다.
사용: i18n_align.py <번역 json> ...   → 파일별 의심 항목 수와 목록"""
import sys, json, re
NUM = re.compile(r'\d+(?:\.\d+)?'); LAT = re.compile(r'[A-Za-z][A-Za-z0-9\-\.]{2,}')
def toks(t):
    t = t.replace(",", "")
    return {n for n in NUM.findall(t) if n not in ("1", "2")} | {w.lower() for w in LAT.findall(t)}
def suspicious(k, v):
    a = toks(k)
    if len(a) < 3: return False
    return len(a & toks(v)) / len(a) < 0.34
for f in sys.argv[1:]:
    d = json.load(open(f, encoding="utf-8"))
    bad = [k for k, v in d.items() if suspicious(k, v)]
    print(f, len(d), "suspicious", len(bad))
    for k in bad[:int(__import__('os').environ.get("SHOW", "4"))]: print("   K:", k[:80], "\n   V:", d[k][:80])
