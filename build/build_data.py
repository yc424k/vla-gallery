import json, glob, re, sys, importlib.util
P = sys.argv[1]; G = sys.argv[2]; OUT = sys.argv[3]
spec = importlib.util.spec_from_file_location("fields", f"{G}/fields.py"); fm = importlib.util.module_from_spec(spec); spec.loader.exec_module(fm)
F = fm.F
spec2 = importlib.util.spec_from_file_location("rl", f"{G}/rl.py"); rm = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(rm)
RL = rm.R
assert len(RL) == 165
spec3 = importlib.util.spec_from_file_location("papers", f"{G}/papers.py"); pm = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(pm)
PT, POWN, PREL = pm.T, pm.OWN, pm.REL
NEW = json.load(open(f"{G}/new_models.json", encoding="utf-8"))
BASE = json.load(open(f"{G}/base_existing.json", encoding="utf-8"))
HF = json.load(open(f"{G}/hf.json", encoding="utf-8"))
AX = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})")
def axp(aid, **kw):
    return dict(k="논문", id=aid, u=f"https://arxiv.org/abs/{aid}", t=PT[aid], **kw)
def src_kind(u):
    if not u: return "공식 문서 없이 기사로만 알려짐"
    if "github" in u: return "GitHub 저장소로만 공개"
    if "huggingface.co" in u: return "Hugging Face 모델 카드로만 공개"
    if u.lower().endswith(".pdf"): return "모델 카드 PDF로만 공개"
    if "model-cards" in u: return "모델 카드로만 공개"
    return "공식 블로그·페이지로만 공개"
rows = []
for f in sorted(glob.glob(f"{P}/rows_w[1-6].jsonl")):
    for l in open(f, encoding="utf-8"):
        if l.strip(): rows.append(json.loads(l))
assert len(rows) == 165 and len(F) == 165, (len(rows), len(F))
rows += [n["row"] for n in NEW]
ORDER = ["참고 기준(2024 이전)","VA","자기회귀·잠재 액션 VLA","π 계열","Flow·Diffusion VLA","산업계 모델","휴머노이드 VLA","휴머노이드 전신 제어기","모바일 매니퓰레이션","내비게이션","2026 신규"]
HK = {"이산 토큰","diffusion","flow matching","회귀","CVAE","잠재 액션","하이브리드","영상 world model","RL 정책","기타","미공개"}
FAM = {"Llama","Gemma","Qwen","InternLM","SmolLM","Phi","PaLI·PaLM","Gemini","Mamba","기타","없음","미공개"}
def slug(s):
    s = s.lower().replace("π*", "pistar").replace("π", "pi").replace("ψ", "psi").replace("ρα","rho-alpha").replace("ω","omega")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "m"
def tier(txt):
    t = txt or ""; out = []
    if re.search(r"Jetson|Orin|Thor|임베디드|NanoPi|FSD|내장 CPU|온보드 GPU|탑재", t): out.append("임베디드·탑재")
    if re.search(r"RTX|A4000|A5000|A6000|4090|5090|3090|3080|3070|2080|2060|4060", t): out.append("데스크톱 GPU")
    if re.search(r"A100|H100|L40|A800|GB200|H200", t): out.append("데이터센터 GPU")
    if re.search(r"TPU|클라우드|Gemini API", t): out.append("클라우드")
    return out
KIND = {"이산 토큰": "ar", "잠재 액션": "ar", "하이브리드": "iter", "flow matching": "iter", "diffusion": "iter", "회귀": "single", "CVAE": "single", "RL 정책": "single", "영상 world model": "wm"}
# 행동 1회에 디코딩하는 토큰 수 (원문 근거가 있는 경우만; 나머지는 기본값)
TOKN = {"openvla": 7, "rt-2": 8, "rt-2-x": 8, "pi0-fast": 45, "spatialvla": 12, "lightnav-0": 5, "uni-navid": 4, "streamvln": 4, "navila": 8, "navid": 5}
def est_params(d):
    kind = KIND.get(d["hk"])
    if d["id"] == "turbovla": kind = "single"
    if kind is None: return None
    has_llm = d["lb"] is not None or (d["fam"] != "없음" and not str(d["llm"] or "").startswith("없음") and bool(re.search(r"VLM|LLM|B\b", str(d["llm"] or ""))))
    if kind == "ar" and not has_llm: kind = "single"   # LLM 없는 토큰 정책은 한 번의 순전파로 모든 토큰을 냄
    head = d["head"] or ""
    mh = re.search(r"(\d+(?:\.\d+)?)\s*([MB])(?![A-Za-z])", head)
    ph = float(mh.group(1)) / (1000 if mh.group(2) == "M" else 1) if mh else None
    P, src = d["pb"], "pb"
    if P is None and d["lb"]:
        P = d["lb"] * 1.15 + ((ph or 0.3) if kind == "iter" else 0); src = "lb"
    if P is None: return None
    K = None
    if kind == "iter":
        mk = re.search(r"(\d+)(?:\s*[–-]\s*\d+)?\s*스텝", head) or re.search(r"DDIM\s*(\d+)", head)
        K = int(mk.group(1)) if mk else 10
        if ph is None or ph >= P: ph = (0.3 if P >= 1.5 else 0.25 * P) if has_llm else 0.7 * P
    n_in = (1500 if d["group"] == "내비게이션" else 600) if has_llm else 64
    n_tok = TOKN.get(d["id"], 5 if d["group"] == "내비게이션" else 7) if kind == "ar" else None
    return dict(P=round(P, 3), src=src, kind=kind, K=K, Ph=round(ph, 3) if ph else None, n_in=n_in, n_tok=n_tok)
data = []; ids = set()
for i, r in enumerate(rows, start=1):
    n = NEW[i - 166] if i > 165 else None
    f = n["fields"] if n else F[i]
    assert f.get("hk","미공개") in HK, (i, f.get("hk")); assert f.get("fam","미공개") in FAM, (i, f.get("fam"))
    sid = slug(r["모델"]); base = sid; k = 2
    while sid in ids: sid = f"{base}-{k}"; k += 1
    ids.add(sid)
    pb = r["파라미터(B)"]
    summ = r["핵심 특징"].strip()
    first = re.split(r"(?<=다\.)\s", summ, maxsplit=1)[0]
    d = dict(id=sid, name=r["모델"], group=r["구분"], gi=ORDER.index(r["구분"]), type=r["유형"], domain=r["도메인"], date=r["발표"], org=r["기관"],
             open=r["가중치 공개"], arch=r["아키텍처"], summary=first, feature=summ, params=r["파라미터"], pb=pb,
             vis=f.get("v"), llm=f.get("l","미공개"), lb=f.get("lb"), fam=f.get("fam","미공개"), trunk=f.get("t"), txt=f.get("txt"), world=f.get("w"),
             head=f.get("h","미공개"), hk=f.get("hk","미공개"), chunk=f.get("ck","미공개"), hz=f.get("hz","미공개"), dep=f.get("dep"),
             infer=r["추론"], tiers=tier(r["추론"] + " " + (f.get("dep") or "")), mem=f.get("mem"), mg=f.get("mg"), mge=bool(f.get("mge")), mq=f.get("mq") or [], mc=f.get("mc", True),
             inp=f.get("inp"), pipe=f.get("pipe"), tags=f.get("tags", []),
             backbone_text=r["백본·액션 표현"],
             pre_hw=r["사전학습 가속기"], pre_time=r["사전학습 기간"], pre_steps=r["사전학습 스텝·배치"], gpuh=r["사전학습 GPU·TPU-시간"], gpuh_basis=r["시간 근거·단위"],
             ft=r["파인튜닝 가속기·시간"], tasks=r["태스크·벤치마크"], robots=r["로봇·엠바디먼트"], dtype=r["데이터 종류"], dscale=r["데이터 규모"], dhours=r["데이터 시간(h)"],
             datasets=r["주요 데이터셋"], note=r["비고"], verify=r["검증"], src=(r["1차 출처 URL"] or "").split(" ;")[0].split()[0] if r["1차 출처 URL"] else None)
    d["w16"] = round(pb * 2, 2) if isinstance(pb, (int, float)) else None
    rr = n["rl"] if n else RL[i]; assert rr[0] in ("사용","일부","미사용","미공개"), (i, rr)
    d["rl"], d["rlcat"], d["rlwhere"] = rr[0], rr[1], rr[2]; d["rlsrc"] = rr[3] if len(rr) > 3 else None
    if d["src"] and not d["src"].startswith("http"): d["src"] = None
    m = AX.search(d["src"] or "")
    if n:
        p = n["paper"]; d["paper"] = dict(k=p["k"], id=p.get("id"), u=p.get("u"), t=p.get("t"), n=p.get("n"))
    elif i in POWN:
        o = dict(POWN[i]); d["paper"] = axp(o["id"]) if o.get("id") else dict(k=o["k"], id=None, u=o["u"], t=o["t"], n=o.get("n"))
    elif m:
        d["paper"] = axp(m.group(1))
    else:
        d["paper"] = dict(k="없음", id=None, u=None, t=None, n=src_kind(d["src"]))
    if n:
        d["prel"] = n.get("prel") or None
    elif i in PREL:
        assert d["paper"]["k"] == "없음", (i, d["name"])
        r = PREL[i]
        d["prel"] = dict(id=r["id"], u=f"https://arxiv.org/abs/{r['id']}", t=PT[r["id"]], why=r["why"]) if r.get("id") else dict(id=None, u=r["u"], t=r["t"], why=r["why"])
    else:
        d["prel"] = None
    d["base"] = n["base"] if n else BASE[str(i)]
    d["est"] = est_params(d)
    d["hf"] = HF.get(d["id"], [])
    assert all(u.startswith("https://huggingface.co/") for u in d["hf"]), d["id"]
    data.append(d)
assert set(HF) <= {d["id"] for d in data}, set(HF) - {d["id"] for d in data}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
# stats
from collections import Counter, defaultdict
def yb(dt):
    y = int(dt[:4]); return "2023 이전" if y <= 2023 else str(y)
fc = defaultdict(Counter)
for d in data:
    if d["fam"] not in ("없음","미공개"): fc[yb(d["date"])][d["fam"]] += 1
for y in sorted(fc): print(y, dict(fc[y]))
tot = Counter(d["fam"] for d in data); print("total fam", dict(tot))
print("mem points", [(d["name"], d["pb"], d["mg"]) for d in data if d["mg"] and d["pb"] and d["mc"]])
print("tiers", Counter(t for d in data for t in d["tiers"]))
print("open", Counter(d["open"] for d in data), "hf", sum(1 for d in data if d["hf"]))
print("hk", Counter(d["hk"] for d in data))
print("paper", Counter(d["paper"]["k"] for d in data), "rel", sum(1 for d in data if d["prel"]))
print("base", Counter(t for d in data for t in d["base"]["types"]), Counter(d["base"].get("cat") for d in data))
print("rl", Counter(d["rl"] for d in data)); print("rlcat", Counter(d["rlcat"] for d in data)); print("size", len(json.dumps(data, ensure_ascii=False)))
