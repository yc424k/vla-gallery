"""Corpus statistics for the paper. Writes ../data/stats.json and ../stats.tex (LaTeX macros)."""
import collections as C, json, math, re, statistics as S
from corpus import D, TG, en, year, macro_domain, sector, disclosed_text, na_text, hz_value, HEAD_ORDER, FAM_ORDER, weights_open, chunk_kind, acc_family, HF
from estimator import DEVICES, DEVBY, ANCHORS, fit_of, tune_of

N = len(D)
st = {}
pct = lambda a, b: 100.0 * a / b if b else float("nan")

# ---------------- composition ----------------
st["n_models"] = N
st["by_year"] = dict(sorted(C.Counter(year(m) for m in D).items()))
st["by_type"] = dict(C.Counter(m["type"] for m in D))
st["by_domain"] = dict(C.Counter(macro_domain(m) for m in D))
st["by_sector"] = dict(C.Counter(sector(m) for m in D))
st["by_group"] = dict(C.Counter(m["group"] for m in D))
st["year_domain"] = {y: dict(C.Counter(macro_domain(m) for m in D if year(m) == y)) for y in sorted(st["by_year"])}
st["open"] = dict(C.Counter(m["open"] for m in D))
st["open_hf_reconciled"] = [m["id"] for m in D if m["open"] == "미확인" and weights_open(m)]
st["n_weights_open"] = sum(weights_open(m) for m in D)
st["n_hf"] = sum(bool(m["hf"]) for m in D)
st["n_gh"] = sum(bool(m["gh"]) for m in D)
st["paper_kind"] = dict(C.Counter(m["paper"]["k"] for m in D))
st["verify"] = dict(C.Counter(m["verify"] for m in D))
st["open_by_sector"] = {s: dict(C.Counter(m["open"] for m in D if sector(m) == s)) for s in st["by_sector"]}
st["weights_open_by_sector"] = {s: [sum(weights_open(m) for m in D if sector(m) == s), sum(1 for m in D if sector(m) == s)] for s in st["by_sector"]}
st["paper_by_sector"] = {s: dict(C.Counter(m["paper"]["k"] for m in D if sector(m) == s)) for s in st["by_sector"]}

# evidence markers across all text fields of a record
def fields_text(m):
    return " ".join(str(v) for k, v in m.items() if isinstance(v, str))
st["n_secondary"] = sum("(2차)" in fields_text(m) for m in D)
st["n_dagger"] = sum("†" in fields_text(m) for m in D)

# ---------------- architecture ----------------
st["head"] = {h: sum(m["hk"] == h for m in D) for h in HEAD_ORDER}
st["fam"] = {f: sum(m["fam"] == f for m in D) for f in FAM_ORDER}
st["arch"] = dict(C.Counter(m["arch"] for m in D))
yrs = [2023, 2024, 2025, 2026]
yr_bucket = lambda m: max(2023, year(m))  # 2022 folded into 2023 (two models)
yb_ = yr_bucket
st["head_by_year"] = {y: dict(C.Counter(m["hk"] for m in D if yr_bucket(m) == y)) for y in yrs}
st["fam_by_year"] = {y: dict(C.Counter(m["fam"] for m in D if yr_bucket(m) == y)) for y in yrs}
vla = [m for m in D if m["type"] == "VLA"]
st["n_vla"] = len(vla)
st["vla_fam"] = dict(C.Counter(m["fam"] for m in vla))
st["vla_head"] = dict(C.Counter(m["hk"] for m in vla))
st["vla_fam_by_year"] = {y: dict(C.Counter(m["fam"] for m in vla if yr_bucket(m) == y)) for y in yrs}
st["vla_head_by_year"] = {y: dict(C.Counter(m["hk"] for m in vla if yr_bucket(m) == y)) for y in yrs}
lb = [m["lb"] for m in D if m["lb"] is not None]
st["llm_size"] = dict(n=len(lb), median=S.median(lb), min=min(lb), max=max(lb), counts=dict(sorted(C.Counter(lb).items())))
pb = [(year(m), m["pb"], m) for m in D if m["pb"] is not None]
st["params"] = dict(n=len(pb), median=S.median([p for _, p, _ in pb]), min=min(p for _, p, _ in pb), max=max(p for _, p, _ in pb),
                    by_year={y: dict(n=len(v), median=S.median(v)) for y in yrs for v in [[p for yy, p, mm in pb if max(2023, yy) == y]] if v},
                    by_type={t: S.median([p for _, p, mm in pb if mm["type"] == t]) for t in ["VLA", "VA", "기타"]},
                    largest=sorted([(p, mm["name"]) for _, p, mm in pb], reverse=True)[:5],
                    lt1=sum(p < 1 for _, p, _ in pb), b1_4=sum(1 <= p < 4 for _, p, _ in pb), b4_10=sum(4 <= p < 10 for _, p, _ in pb), ge10=sum(p >= 10 for _, p, _ in pb))
st["params_vla_median"] = S.median([m["pb"] for m in vla if m["pb"] is not None])
# action chunking
st["chunk"] = dict(C.Counter(chunk_kind(m) for m in D))
st["chunk_share_by_year"] = {y: [sum(chunk_kind(m) == "chunked" for m in D if yb_(m) == y), sum(chunk_kind(m) != "undisclosed" for m in D if yb_(m) == y)] for y in [2023, 2024, 2025, 2026]}
# control rates
hz = [(m, hz_value(m)) for m in D]
hzv = [h for _, h in hz if h is not None]
st["hz"] = dict(n=len(hzv), median=S.median(hzv), ge30=sum(h >= 30 for h in hzv), ge10=sum(h >= 10 for h in hzv), lt5=sum(h < 5 for h in hzv),
                by_head={h: S.median(v) for h in HEAD_ORDER for v in [[x for m, x in hz if x is not None and m["hk"] == h]] if len(v) >= 3})
st["hz_disclosed"] = sum(not m["hz"].startswith("미공개") for m in D)
# hierarchical / dual-system pipelines (pipe field lists >1 learned stage)
st["n_pipe"] = sum(m["pipe"] is not None for m in D)

# ---------------- training resources ----------------
recs = [(mid, r) for mid, rs in TG.items() for r in rs]
st["tg_models"] = len(TG)
st["tg_records"] = len(recs)
st["tg_stage"] = dict(C.Counter(r["st"] for _, r in recs))
st["tg_acc_family"] = dict(C.Counter(acc_family(r["acc"]) for _, r in recs))
pre = [r for _, r in recs if r["st"] == "사전학습"]
st["tg_pre_acc_family"] = dict(C.Counter(acc_family(r["acc"]) for r in pre))
def num(x):
    if x is None: return None
    return math.sqrt(x[0] * x[1]) if isinstance(x, list) else x
pre_n = [num(r.get("n")) for r in pre if num(r.get("n")) is not None]
pre_h = [num(r.get("h")) for r in pre if num(r.get("h")) is not None]
st["tg_pre_n"] = dict(n=len(pre_n), median=S.median(pre_n), max=max(pre_n), min=min(pre_n), ge64=sum(x >= 64 for x in pre_n), le8=sum(x <= 8 for x in pre_n))
st["tg_pre_h"] = dict(n=len(pre_h), median=S.median(pre_h), max=max(pre_h), min=min(pre_h))
ft = [r for _, r in recs if r["st"] in ("파인튜닝", "과제별 학습")]
ft_n = [num(r.get("n")) for r in ft if num(r.get("n")) is not None]
ft_h = [num(r.get("h")) for r in ft if num(r.get("h")) is not None]
st["tg_ft_n"] = dict(n=len(ft_n), median=S.median(ft_n), le1=sum(x <= 1 for x in ft_n), le8=sum(x <= 8 for x in ft_n))
st["tg_ft_h"] = dict(n=len(ft_h), median=S.median(ft_h))
st["tg_simrl_family"] = dict(C.Counter(acc_family(r["acc"]) for _, r in recs if r["st"] == "시뮬 RL"))
simrl = [r for _, r in recs if r["st"] == "시뮬 RL"]
st["tg_simrl_n"] = dict(n=len([1 for r in simrl if num(r.get("n")) is not None]), median=S.median([num(r.get("n")) for r in simrl if num(r.get("n")) is not None]),
                        acc=dict(C.Counter(acc_family(r["acc"]) for r in simrl)))
gp = [(m, m["gpuh"]) for m in D if m["gpuh"] is not None]
gv = sorted(g for _, g in gp)
q1, q3 = (float(v) for v in __import__("numpy").percentile(gv, [25, 75]))
st["gpuh"] = dict(n=len(gv), median=S.median(gv), min=min(gv), max=max(gv), q1=q1, q3=q3,
                  top=sorted([(g, m["name"]) for m, g in gp], reverse=True)[:6], bottom=sorted([(g, m["name"]) for m, g in gp])[:4],
                  ge10k=sum(g >= 1e4 for g in gv), lt1k=sum(g < 1e3 for g in gv))
# GPU-hours vs parameters (log-log Spearman)
def spearman(x, y):
    rx = {v: i for i, v in enumerate(sorted(x))}; ry = {v: i for i, v in enumerate(sorted(y))}
    def rank(a):
        srt = sorted(range(len(a)), key=lambda i: a[i]); r = [0] * len(a)
        i = 0
        while i < len(a):
            j = i
            while j + 1 < len(a) and a[srt[j + 1]] == a[srt[i]]: j += 1
            for k in range(i, j + 1): r[srt[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rank(x), rank(y)
    ma, mb = S.mean(a), S.mean(b)
    num_ = sum((p - ma) * (q - mb) for p, q in zip(a, b)); den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num_ / den
pairs = [(m["pb"], g) for m, g in gp if m["pb"]]
st["gpuh_vs_params"] = dict(n=len(pairs), spearman=spearman([p for p, _ in pairs], [g for _, g in pairs]))
pairs_y = [(int(m["date"][:4]) + (int(m["date"][5:7]) - 1) / 12, g) for m, g in gp if re.match(r"\d{4}-\d{2}", m["date"])]
st["gpuh_vs_date"] = dict(n=len(pairs_y), spearman=spearman([p for p, _ in pairs_y], [g for _, g in pairs_y]))
pairs_d = [(m["gpuh"], m["dhours"]) for m in D if m["gpuh"] and m["dhours"]]
st["gpuh_vs_dhours"] = dict(n=len(pairs_d), spearman=spearman([a for a, _ in pairs_d], [b for _, b in pairs_d]))
dh = [m["dhours"] for m in D if m["dhours"] is not None]
st["dhours"] = dict(n=len(dh), median=S.median(dh), max=max(dh), ge10k=sum(x >= 1e4 for x in dh),
                   by_year={y: dict(n=len(v), median=S.median(v)) for y in [2023, 2024, 2025, 2026] for v in [[m["dhours"] for m in D if m["dhours"] is not None and max(2023, year(m)) == y]] if v})
def dtype_tags(m):
    s = m["dtype"]; t = set()
    if "텔레옵" in s or "실로봇" in s: t.add("Real-robot teleoperation")
    if "시뮬" in s or "합성" in s: t.add("Simulation/synthetic")
    if "사람" in s or "인간" in s or "egocentric" in s.lower() or "1인칭" in s: t.add("Human video")
    if "웹" in s: t.add("Web vision-language")
    if "모션캡처" in s or "모캡" in s: t.add("Motion capture")
    if s.startswith("미공개") or s.startswith("미확인"): t.add("Not disclosed")
    return t or {"Other"}
st["dtype"] = dict(C.Counter(t for m in D for t in dtype_tags(m)))

# ---------------- disclosure matrix ----------------
def has_tg(m, key=None):
    rs = TG.get(m["id"], [])
    if key is None: return bool(rs)
    return any(r.get(key) is not None for r in rs)
ITEMS = [
    ("Parameter count", lambda m: m["pb"] is not None),
    ("Backbone (V)LM", lambda m: m["fam"] != "미공개"),
    ("Action-head type", lambda m: m["hk"] != "미공개"),
    ("Training accelerator", lambda m: has_tg(m) and any(r["acc"] != "기종 미공개" for r in TG[m["id"]])),
    ("Training duration", lambda m: has_tg(m, "h")),
    ("GPU/TPU-hours", lambda m: m["gpuh"] is not None),
    ("Training data scale", lambda m: disclosed_text(m["dscale"])),
    ("Control rate", lambda m: not m["hz"].startswith("미공개")),
    ("Inference hardware", lambda m: bool(m["tiers"])),
    ("Inference memory", lambda m: m["mem"] is not None),
    ("Open weights", weights_open),
    ("Code repository", lambda m: bool(m["gh"])),
]
st["disclosure_items"] = [k for k, _ in ITEMS]
st["disclosure_overall"] = {k: sum(f(m) for m in D) for k, f in ITEMS}
grp = {"Academic": [m for m in D if sector(m) == "Academic"], "Mixed": [m for m in D if sector(m) == "Mixed"], "Industry": [m for m in D if sector(m) == "Industry"]}
st["disclosure_by_sector"] = {g: {k: sum(f(m) for m in ms) for k, f in ITEMS} | {"_n": len(ms)} for g, ms in grp.items()}
st["disclosure_by_year"] = {y: {k: sum(f(m) for m in ms) for k, f in ITEMS} | {"_n": len(ms)} for y in yrs for ms in [[m for m in D if yr_bucket(m) == y]]}
st["disclosure_by_domain"] = {g: {k: sum(f(m) for m in ms) for k, f in ITEMS} | {"_n": len(ms)} for g in ["Manipulation", "Humanoid", "Mobile manipulation", "Navigation"] for ms in [[m for m in D if macro_domain(m) == g]]}
st["disclosure_trend_by_sector"] = {y: {g: {k: [sum(f(m) for m in D if yr_bucket(m) == y and sector(m) in gs), sum(1 for m in D if yr_bucket(m) == y and sector(m) in gs)]
                                           for k, f in ITEMS} for g, gs in [("Industry", ("Industry",)), ("Other", ("Academic", "Mixed"))]} for y in yrs}
st["industry_share_by_year"] = {y: [sum(1 for m in D if yr_bucket(m) == y and sector(m) == "Industry"), sum(1 for m in D if yr_bucket(m) == y)] for y in yrs}
score = {m["id"]: sum(f(m) for _, f in ITEMS) for m in D}
st["disclosure_score"] = dict(median=S.median(score.values()), by_sector={g: S.median([score[m["id"]] for m in ms]) for g, ms in grp.items()})
# items needed to compute GPU-hours: accelerator count and duration in the same record
st["n_count_and_duration"] = sum(any(r.get("n") is not None and r.get("h") is not None for r in TG.get(m["id"], [])) for m in D)
st["n_est"] = sum(m["est"] is not None for m in D)
st["est_kind"] = dict(C.Counter((m["est"] or {}).get("kind") for m in D))
st["est_src"] = dict(C.Counter((m["est"] or {}).get("src") for m in D))

# ---------------- RL ----------------
st["rl"] = dict(C.Counter(m["rl"] for m in D))
st["rlcat"] = dict(C.Counter(m["rlcat"] for m in D))
st["rl_by_year"] = {y: dict(C.Counter(m["rl"] for m in D if yr_bucket(m) == y)) for y in yrs}
st["rlcat_by_domain"] = {g: dict(C.Counter(m["rlcat"] for m in D if macro_domain(m) == g)) for g in ["Manipulation", "Humanoid", "Mobile manipulation", "Navigation"]}
st["rl_by_domain"] = {g: dict(C.Counter(m["rl"] for m in D if macro_domain(m) == g)) for g in ["Manipulation", "Humanoid", "Mobile manipulation", "Navigation"]}
st["vla_rl_post"] = [m["name"] for m in D if m["rlcat"] == "VLA RL 사후학습"]
st["vla_rl_post_by_year"] = dict(C.Counter(year(m) for m in D if m["rlcat"] == "VLA RL 사후학습"))

# ---------------- mobile base ----------------
st["base_types"] = dict(C.Counter(t for m in D for t in m["base"]["types"]))
mob = [m for m in D if any(t != "고정" for t in m["base"]["types"])]
st["n_mobile"] = len(mob)
st["base_cat"] = dict(C.Counter(m["base"]["cat"] for m in mob))
st["base_cat_by_type"] = {t: dict(C.Counter(m["base"]["cat"] for m in mob if t in m["base"]["types"])) for t in ["바퀴형", "사족보행", "휴머노이드 보행", "비행", "시뮬 전용"]}
st["base_checked"] = sum(bool(m["base"].get("checked")) for m in mob)

# ---------------- deployability matrix ----------------
SHOW = ["jetson-orin-nano-super", "jetson-orin-nx-16", "jetson-agx-orin-64", "jetson-agx-thor", "rtx-4060-laptop", "rtx-4090-laptop",
        "rtx-4090", "rtx-5090", "rtx-pro-6000", "a100-80", "h100-sxm"]
SHOW = [d for d in SHOW if d in DEVBY]
ASSESS = [m for m in D if m["est"] and m["est"]["kind"] != "wm"]  # models with a latency estimate
st["n_assess"] = len(ASSESS)
st["est_none_nosize"] = sum(1 for m in D if not m["est"] and m["pb"] is None and m["lb"] is None)
st["est_none_nokind"] = [m["id"] for m in D if not m["est"] and not (m["pb"] is None and m["lb"] is None)]
dep = {}
for did in SHOW:
    dev = DEVBY[did]
    for b in (2, 1, 0.5):
        for thr in (5, 10):
            r = [fit_of(m, dev, b, thr) for m in ASSESS]
            dep[f"{did}|{b}|{thr}"] = dict(C.Counter(x["v"] for x in r))
st["deploy"] = dep
st["deploy_devices"] = [dict(id=d, name=DEVBY[d]["name"], tier=DEVBY[d]["tier"], mem=DEVBY[d]["mem_gb"], bw=DEVBY[d]["bw_gbs"], tf=DEVBY[d]["bf16_tflops"]) for d in SHOW]
st["n_devices"] = len(DEVICES)
st["n_anchor_models"] = len(set(a[0] for a in ANCHORS))
st["n_anchors"] = len(ANCHORS)
st["anchor_devices"] = len(set(a[1] for a in ANCHORS))

# ---------------- fine-tuning feasibility ----------------
TCFG = [("rtx-4090", 1), ("rtx-5090", 1), ("a100-80", 1), ("h100-sxm", 8), ("jetson-agx-thor", 1)]
tune = {}
for did, n in TCFG:
    if did not in DEVBY: continue
    for meth in ("full", "lora", "qlora", "head"):
        r = [tune_of(dict(m, open="일부") if weights_open(m) and m["open"] == "미확인" else m, DEVBY[did], n, meth, "n", None) for m in D]
        c = C.Counter(x["v"] for x in r)
        hrs = [x["hrs"] for x in r if x["v"] == "ok" and x.get("hrs") is not None]
        okP = [m["est"]["P"] for m, x in zip(D, r) if x["v"] == "ok"]
        tune[f"{did}|{n}|{meth}"] = dict(c, med_hrs=S.median(hrs) if hrs else None, max_P=max(okP) if okP else None)
st["tune"] = tune
st["n_open_est"] = sum(1 for m in D if m["est"] and weights_open(m))

json.dump(st, open("../data/stats.json", "w"), indent=1, ensure_ascii=False, default=str)

# ---------------- LaTeX macros ----------------
cal = json.load(open("../data/calibration.json"))
mac = {}
def M(name, val):
    mac[name] = val
M("nModels", N); M("nVLA", st["by_type"]["VLA"]); M("nVA", st["by_type"]["VA"]); M("nOther", st["by_type"]["기타"])
for y, c in st["by_year"].items(): M("nY" + "ABCDEFGHIJ"[y - 2020], c)  # nYC=2022 ... nYG=2026
for k, nm in [("Manipulation", "nManip"), ("Humanoid", "nHum"), ("Mobile manipulation", "nMoMa"), ("Navigation", "nNav")]: M(nm, st["by_domain"][k])
for k, nm in [("Industry", "nInd"), ("Academic", "nAcad"), ("Mixed", "nMixed"), ("Unknown", "nUnk")]: M(nm, st["by_sector"].get(k, 0))
M("nOpenYes", st["open"]["예"]); M("nOpenPart", st["open"]["일부"]); M("nOpenNo", st["open"]["아니오"]); M("nOpenUnk", st["open"]["미확인"])
M("nHF", st["n_hf"]); M("nGH", st["n_gh"]); M("nPaper", st["paper_kind"]["논문"]); M("nReport", st["paper_kind"].get("보고서", 0)); M("nNoPaper", st["paper_kind"]["없음"])
M("nVerified", st["verify"]["확인"]); M("nCorrected", st["verify"]["수정 반영"]); M("nUnverified", st["verify"]["미검증"] + st["verify"].get("확인불가", 0))
M("nSecondary", st["n_secondary"]); M("nDagger", st["n_dagger"])
M("nParams", st["params"]["n"]); M("medParams", f'{st["params"]["median"]:.1f}'); M("medParamsVLA", f'{st["params_vla_median"]:.1f}')
M("nLLMsize", st["llm_size"]["n"]); M("medLLM", f'{st["llm_size"]["median"]:g}')
M("nTGmodels", st["tg_models"]); M("nTGrecords", st["tg_records"])
M("nGPUh", st["gpuh"]["n"]); M("medGPUh", f'{st["gpuh"]["median"]:,.0f}'); M("qOneGPUh", f'{st["gpuh"]["q1"]:,.0f}'); M("qThreeGPUh", f'{st["gpuh"]["q3"]:,.0f}'); M("maxGPUh", f'{st["gpuh"]["max"]:,.0f}'); M("minGPUh", f'{st["gpuh"]["min"]:,.0f}')
M("rhoGpuhParams", f'{st["gpuh_vs_params"]["spearman"]:.2f}'); M("nGpuhParams", st["gpuh_vs_params"]["n"])
M("rhoGpuhDate", f'{st["gpuh_vs_date"]["spearman"]:.2f}'); M("rhoGpuhData", f'{st["gpuh_vs_dhours"]["spearman"]:.2f}'); M("nGpuhData", st["gpuh_vs_dhours"]["n"])
M("nHz", st["hz"]["n"]); M("medHz", f'{st["hz"]["median"]:g}')
M("nEst", st["n_est"]); M("nAnchors", st["n_anchors"]); M("nAnchorsValid", cal["current"]["n"]); M("nAnchorModels", st["n_anchor_models"]); M("nAnchorDevices", st["anchor_devices"])
M("nDevices", st["n_devices"])
M("calMed", f'{cal["current"]["median_x"]:.2f}'); M("calWithinTwo", cal["current"]["within2"]); M("calWithinOneFive", cal["current"]["within1_5"])
M("calBias", f'{cal["current"]["bias_gm"]:.2f}'); M("looMed", f'{cal["loo"]["median_x"]:.2f}'); M("looWithinTwo", cal["loo"]["within2"])
M("nomMed", f'{cal["nominal"]["median_x"]:.2f}'); M("nomWithinTwo", cal["nominal"]["within2"])
M("trMed", f'{cal["transfer"]["median_x"]:.2f}'); M("trN", cal["transfer"]["n"]); M("trWithinTwo", cal["transfer"]["within2"])
M("refitMed", f'{cal["refit_median"]["median_x"]:.2f}')
M("nRLuse", st["rl"]["사용"]); M("nRLpart", st["rl"]["일부"]); M("nRLnone", st["rl"]["미사용"]); M("nRLund", st["rl"]["미공개"])
M("nMobile", st["n_mobile"])
M("nAssess", st["n_assess"]); M("nNoSize", st["est_none_nosize"]); M("nNoKind", len(st["est_none_nokind"])); M("nNotAssessable", st["est_none_nosize"] + len(st["est_none_nokind"]))
M("nWeightsOpen", st["n_weights_open"]); M("nOpenHF", len(st["open_hf_reconciled"])); M("nOpenEst", st["n_open_est"])
M("memN", cal["memory"]["n"]); M("memNbf", cal["memory"]["n_bf16"]); M("memMed", f'{cal["memory"]["median_x"]:.2f}'); M("memWithinOneFive", cal["memory"]["within1_5"])
M("memWithinTwo", cal["memory"]["within2"]); M("memBias", f'{cal["memory"]["bias_gm"]:.2f}')
M("holdPred", f'{cal["holdout"]["predicted_ms"]:.0f}'); M("holdMeas", f'{cal["holdout"]["measured_ms"]:.0f}')
rc = cal["refit_median"]["consts"]
M("refitBeta", f'{rc["em"]:g}'); M("refitPhi", f'{rc["ec"]:g}'); M("refitCzero", f'{rc["c0"]:g}'); M("refitCt", f'{rc["ct"]:g}'); M("refitGamma", f'{rc["emb"]:g}')
with open("../stats.tex", "w") as f:
    f.write("% Auto-generated by scripts/analysis.py from gallery/data.json -- do not edit by hand\n")
    for k, v in mac.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(json.dumps({k: st[k] for k in ["by_year", "by_type", "by_domain", "by_sector", "open", "n_hf", "n_gh", "paper_kind", "verify", "n_secondary", "n_dagger", "head", "fam", "llm_size", "params", "params_vla_median", "chunk", "hz", "hz_disclosed", "n_pipe"]}, indent=0, ensure_ascii=False, default=str))
