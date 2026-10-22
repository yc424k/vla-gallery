"""Python port of the deployment-feasibility estimator used by the VLA gallery
(gallery/template.html: estLatency, fitOf, tuneOf). Kept line-for-line close to
the JavaScript so that numbers in the paper match the web page."""
import json, math, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = json.load(open(os.path.join(ROOT, "gallery", "data.json")))
DEVICES = json.load(open(os.path.join(ROOT, "gallery", "devices.json")))
DEVBY = {d["id"]: d for d in DEVICES}
BYID = {m["id"]: m for m in D}


def _anchors():
    """Read the ANCHORS array (model id, device id, bytes/param, latency ms, label)
    straight from template.html so the paper never drifts from the page."""
    src = open(os.path.join(ROOT, "gallery", "template.html"), encoding="utf-8").read()
    block = src[src.index("const ANCHORS = ["):src.index("];", src.index("const ANCHORS = ["))]
    out = []
    for m in re.finditer(r'\["([^"]+)","([^"]+)",([\d.]+),([\d.]+),', block):
        out.append((m.group(1), m.group(2), float(m.group(3)), float(m.group(4))))
    return out


ANCHORS = _anchors()
EST = dict(em=0.6, ec=0.6, c0=4.0, ct=4.0, emb=1.5)
TUNE = dict(act={"s": (2, 1.5), "n": (4, 5)}, lora=0.01, mfu=0.35, scale=0.9, steps=10000, batch=32, nh=64)


def is_emb(dev):
    return dev["tier"] == "임베디드"


def est_latency(m, dev, b, C=EST):
    e = m.get("est")
    if not e or e["kind"] == "wm":
        return None
    bw, tf = dev["bw_gbs"] * C["em"], dev["bf16_tflops"] * C["ec"]
    tm = lambda p: 1000 * p * b / bw
    tc = lambda p, n: 2 * p * n / tf
    fwd = lambda p, n: max(tm(p), tc(p, n)) + C["c0"]
    if e["kind"] == "ar":
        L = fwd(e["P"], e["n_in"]) + e["n_tok"] * (tm(e["P"]) + C["ct"])
    elif e["kind"] == "iter":
        L = fwd(max(e["P"] - e["Ph"], 0.01), e["n_in"]) + e["K"] * fwd(e["Ph"], 50)
    else:
        L = fwd(e["P"], e["n_in"])
    return L * (C["emb"] if is_emb(dev) else 1)


def mem_need(m, b):
    return m["est"]["P"] * b + 1 + 0.3 * m["est"]["P"]


def fit_of(m, dev, b, thr, use_anchors=True, C=EST):
    """Returns dict with v in {ok, slow, oom, na}, mem, L (ms), hz, basis."""
    if not m.get("est"):
        return dict(v="na")
    mem = mem_need(m, b)
    r = dict(mem=mem, fits=mem <= dev["mem_gb"] * (0.75 if is_emb(dev) else 0.9))
    an = [a for a in ANCHORS if a[0] == m["id"] and a[1] in DEVBY] if use_anchors else []
    exact = next((a for a in an if a[1] == dev["id"] and a[2] == b), None)
    L, basis = None, "estimate"
    if exact:
        L, basis = exact[3], "measured"
    elif an:
        sc = []
        for a in an:
            d0 = DEVBY[a[1]]
            s = abs(math.log(d0["bw_gbs"] / dev["bw_gbs"]))
            if a[2] != b:
                s += 0.7
            if is_emb(d0) != is_emb(dev):
                s += 0.5
            sc.append((s, a, d0))
        sc.sort(key=lambda x: x[0])
        _, a, d0 = sc[0]
        e0, e1 = est_latency(m, d0, a[2], C), est_latency(m, dev, b, C)
        if e0 and e1:
            L, basis = a[3] * e1 / e0, "rescaled"
    if L is None:
        L = est_latency(m, dev, b, C)
    if L is None:
        r["v"] = "na" if r["fits"] else "oom"
        return r
    r.update(L=L, hz=1000 / L, basis=basis)
    r["v"] = "oom" if not r["fits"] else ("ok" if r["hz"] >= thr else "slow")
    return r


def tune_of(m, dev, N, meth, bs="n", lim=None):
    e = m.get("est")
    if not e:
        return dict(v="na")
    P, a = e["P"], TUNE["act"][bs]
    it = e["kind"] == "iter" and (e.get("Ph") or 0) > 0
    Ph = min(e["Ph"], P) if it else 0
    Pb = P - Ph
    if meth == "head":
        if not it:
            return dict(v="na")
        mem = 2 * Pb + 16 * Ph / N + a[0] + 0.3 * P + a[1] * Ph
        train = Ph
        fl = 2 * Pb * e["n_in"] + 6 * Ph * TUNE["nh"]
    else:
        act = a[0] + a[1] * P
        ad = 16 * TUNE["lora"] * P
        if meth == "full":
            mem = 16 * P / N + act
            train = P
            fl = 6 * Pb * e["n_in"] + 6 * Ph * TUNE["nh"]
        else:
            mem = (0.55 if meth == "qlora" else 2) * P + ad + act
            train = TUNE["lora"] * P
            fl = (4 * Pb * e["n_in"] + 4 * Ph * TUNE["nh"]) * (1.3 if meth == "qlora" else 1)
    r = dict(mem=mem, train=train, fits=mem <= dev["mem_gb"] * (0.75 if is_emb(dev) else 0.9))
    if e["kind"] != "wm":
        eff = dev["bf16_tflops"] * TUNE["mfu"] / (EST["emb"] if is_emb(dev) else 1) * N * (TUNE["scale"] if N > 1 else 1)
        r["hrs"] = fl * 1e9 * TUNE["steps"] * TUNE["batch"] / (eff * 1e12) / 3600
    opn = m["open"] in ("예", "일부")
    if not opn:
        r["v"] = "closed"
    elif not r["fits"]:
        r["v"] = "oom"
    elif lim and r.get("hrs") is not None and r["hrs"] > lim:
        r["v"] = "slow"
    else:
        r["v"] = "ok"
    return r
