"""Calibration, leave-one-out validation and ablations for the latency estimator."""
import itertools, json, math, statistics as S
import numpy as np
from estimator import ANCHORS, BYID, DEVBY, EST, est_latency, is_emb

V = [a for a in ANCHORS if est_latency(BYID[a[0]], DEVBY[a[1]], a[2]) is not None]
GRID = dict(em=np.round(np.arange(0.3, 1.01, 0.1), 2), ec=np.round(np.arange(0.2, 1.01, 0.1), 2),
            c0=np.arange(0, 11, 1.0), ct=np.arange(0, 11, 1.0), emb=np.array([1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]))
keys = list(GRID)
combo = np.array(list(itertools.product(*[GRID[k] for k in keys])))  # (G, 5)
C = {k: combo[:, i] for i, k in enumerate(keys)}


def lat_vec(m, dev, b):
    e = m["est"]
    bw, tf = dev["bw_gbs"] * C["em"], dev["bf16_tflops"] * C["ec"]
    tm = lambda p: 1000 * p * b / bw
    tc = lambda p, n: 2 * p * n / tf
    fwd = lambda p, n: np.maximum(tm(p), tc(p, n)) + C["c0"]
    if e["kind"] == "ar":
        L = fwd(e["P"], e["n_in"]) + e["n_tok"] * (tm(e["P"]) + C["ct"])
    elif e["kind"] == "iter":
        L = fwd(max(e["P"] - e["Ph"], 0.01), e["n_in"]) + e["K"] * fwd(e["Ph"], 50)
    else:
        L = fwd(e["P"], e["n_in"])
    return L * (C["emb"] if is_emb(dev) else 1.0)


E = np.array([np.log(lat_vec(BYID[a[0]], DEVBY[a[1]], a[2]) / a[3]) for a in V])  # (n, G)
A = np.abs(E)


def summary(err):
    r = np.exp(np.abs(err))
    return dict(n=int(len(r)), median_x=float(np.median(r)), within2=int((r <= 2).sum()), within1_5=int((r <= 1.5).sum()),
                bias_gm=float(np.exp(np.mean(err))), max_x=float(r.max()))


def at(consts):
    return np.array([math.log(est_latency(BYID[a[0]], DEVBY[a[1]], a[2], consts) / a[3]) for a in V])


out = {}
out["current"] = summary(at(EST)); out["current"]["consts"] = EST
out["nominal"] = summary(at(dict(em=1.0, ec=1.0, c0=0.0, ct=0.0, emb=1.0)))
g = int(np.argmin(np.median(A, axis=0)))
out["refit_median"] = summary(E[:, g]); out["refit_median"]["consts"] = {k: float(C[k][g]) for k in keys}
# leave-one-out: refit on n-1 anchors, predict the held-out one
loo = []
for i in range(len(V)):
    mask = np.ones(len(V), bool); mask[i] = False
    gi = int(np.argmin(np.median(A[mask], axis=0)))
    loo.append(E[i, gi])
out["loo"] = summary(np.array(loo))


# ablations with nominal and calibrated constants: memory-only, compute-only, single-pass roofline
def ablate(mode, consts):
    errs = []
    for a in V:
        m, dev, b = BYID[a[0]], DEVBY[a[1]], a[2]
        e = m["est"]
        bw, tf = dev["bw_gbs"] * consts["em"], dev["bf16_tflops"] * consts["ec"]
        if mode == "memory_only":
            L = 1000 * e["P"] * b / bw
        elif mode == "compute_only":
            L = 2 * e["P"] * e["n_in"] / tf
        elif mode == "single_pass":
            L = max(1000 * e["P"] * b / bw, 2 * e["P"] * e["n_in"] / tf) + consts["c0"]
        L *= consts["emb"] if is_emb(dev) else 1
        errs.append(math.log(L / a[3]))
    return summary(np.array(errs))


nom = dict(em=1.0, ec=1.0, c0=0.0, ct=0.0, emb=1.0)
out["ablation"] = {mode: {"nominal": ablate(mode, nom), "calibrated": ablate(mode, EST)} for mode in ["memory_only", "compute_only", "single_pass"]}

# cross-device transfer: predict each anchor from the nearest other anchor of the same model (fitOf logic)
tr = []
for a in V:
    others = [o for o in V if o[0] == a[0] and o is not a]
    if not others:
        continue
    dev = DEVBY[a[1]]
    sc = []
    for o in others:
        d0 = DEVBY[o[1]]
        s = abs(math.log(d0["bw_gbs"] / dev["bw_gbs"])) + (0.7 if o[2] != a[2] else 0) + (0.5 if is_emb(d0) != is_emb(dev) else 0)
        sc.append((s, o))
    sc.sort(key=lambda x: x[0])
    o = sc[0][1]
    m = BYID[a[0]]
    pred = o[3] * est_latency(m, dev, a[2]) / est_latency(m, DEVBY[o[1]], o[2])
    tr.append(math.log(pred / a[3]))
out["transfer"] = summary(np.array(tr))
# memory equation (1) against reported inference memory: exact bf16/fp16 figures plus reported quantised figures
from estimator import mem_need
from corpus import D as CORPUS
QB = {"int8": 1.0, "int4": 0.5, "4-bit": 0.5, "W4A16": 0.5}
mem_rows = []
for m in CORPUS:
    if m["mg"] is not None and m["est"] and not m["mge"] and m["mc"] is not False:
        mem_rows.append(dict(model=m["id"], bytes=2.0, reported_gb=m["mg"], predicted_gb=mem_need(m, 2)))
        for lab, gb in m["mq"]:
            if lab in QB:
                mem_rows.append(dict(model=m["id"], bytes=QB[lab], reported_gb=gb, predicted_gb=mem_need(m, QB[lab])))
me = np.array([math.log(r["predicted_gb"] / r["reported_gb"]) for r in mem_rows])
out["memory"] = summary(me); out["memory"]["n_bf16"] = sum(r["bytes"] == 2 for r in mem_rows); out["memory_rows"] = mem_rows

# which term dominates the estimate (calibrated constants)
def terms(m, dev, b):
    e = m["est"]; bw, tf = dev["bw_gbs"] * EST["em"], dev["bf16_tflops"] * EST["ec"]
    tm = lambda p: 1000 * p * b / bw
    tc = lambda p, n: 2 * p * n / tf
    if e["kind"] == "ar":
        return {"prefill": max(tm(e["P"]), tc(e["P"], e["n_in"])), "decode": e["n_tok"] * tm(e["P"]), "overhead": EST["c0"] + e["n_tok"] * EST["ct"]}, tc(e["P"], e["n_in"]) > tm(e["P"])
    if e["kind"] == "iter":
        pb = max(e["P"] - e["Ph"], 0.01)
        return {"backbone": max(tm(pb), tc(pb, e["n_in"])), "head": e["K"] * max(tm(e["Ph"]), tc(e["Ph"], 50)), "overhead": EST["c0"] * (1 + e["K"])}, tc(e["Ph"], 50) > tm(e["Ph"])
    return {"pass": max(tm(e["P"]), tc(e["P"], e["n_in"])), "overhead": EST["c0"]}, tc(e["P"], e["n_in"]) > tm(e["P"])
brk = {}
for a in V:
    t, cb = terms(BYID[a[0]], DEVBY[a[1]], a[2])
    k = BYID[a[0]]["est"]["kind"]
    brk.setdefault(k, {"n": 0, "largest": {}, "compute_bound_flag": 0})
    brk[k]["n"] += 1
    big = max(t, key=t.get)
    brk[k]["largest"][big] = brk[k]["largest"].get(big, 0) + 1
    brk[k]["compute_bound_flag"] += int(cb)  # ar/single: prefill compute-bound; iter: head pass compute-bound
out["breakdown"] = brk

# a published measurement that meets the anchor criteria but was not used for calibration
ALOHA = ("aloha-unleashed", "rtx-4090", 2.0, 43.0)
pa = est_latency(BYID[ALOHA[0]], DEVBY[ALOHA[1]], ALOHA[2])
out["holdout"] = dict(model=ALOHA[0], device=ALOHA[1], measured_ms=ALOHA[3], predicted_ms=pa, ratio=pa / ALOHA[3])

out["per_anchor"] = [dict(model=a[0], device=a[1], bytes=a[2], measured_ms=a[3], predicted_ms=float(est_latency(BYID[a[0]], DEVBY[a[1]], a[2])),
                          kind=BYID[a[0]]["est"]["kind"], tier=DEVBY[a[1]]["tier"]) for a in V]
json.dump(out, open("../data/calibration.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != "per_anchor"}, indent=1))
