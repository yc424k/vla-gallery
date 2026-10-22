"""Figures for the paper (vector PDF + 300-dpi PNG) from the gallery data.
Palette: reference categorical slots in fixed order (validated on white, adjacent and
3-slot all-pairs); grays only for 'not disclosed' / 'other' / 'not used'."""
import json, math, re, collections as C
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from corpus import D, TG, en, year, macro_domain, sector
from estimator import DEVBY, BYID

OUT = "../figures/"
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
GRAY_DARK, GRAY_LIGHT = "#a3a29b", "#d6d5ce"
BLUE_RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
fam = "Liberation Sans" if any("Liberation Sans" == f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": fam, "font.size": 8, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.linewidth": 0.6,
                     "xtick.color": INK2, "ytick.color": INK2, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.titlesize": 8.5, "axes.titleweight": "bold",
                     "axes.titlecolor": INK, "legend.frameon": False, "legend.fontsize": 7.2, "pdf.fonttype": 42,
                     "savefig.dpi": 300, "axes.spines.top": False, "axes.spines.right": False, "text.color": INK})
W_FULL, W_TEXT = 6.85, 5.3  # inches: MDPI full width (~17.4 cm) and text width (~13.5 cm)


def grid(ax, axis="y"):
    ax.grid(axis=axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(OUT + name + ".pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT + name + ".png", bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)


def panel(ax, letter):
    ax.text(-0.02, 1.04, f"({letter})", transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, fontweight="bold", color=INK)


def stacked_bars(ax, cats, series, colors, horizontal=False, pct=False, width=0.68):
    """series: list of (label, values per category)."""
    import numpy as np
    tot = np.array([sum(s[1][i] for s in series) for i in range(len(cats))], dtype=float)
    base = np.zeros(len(cats))
    for (lab, vals), col in zip(series, colors):
        v = np.array(vals, dtype=float)
        if pct:
            v = 100 * v / np.where(tot == 0, 1, tot)
        if horizontal:
            ax.barh(range(len(cats)), v, left=base, color=col, height=width, edgecolor="white", linewidth=0.8, label=lab)
        else:
            ax.bar(range(len(cats)), v, bottom=base, color=col, width=width, edgecolor="white", linewidth=0.8, label=lab)
        base += v
    return tot


# ---------------------------------------------------------------- Fig 2 composition
def fig_composition():
    fig, (a, b) = plt.subplots(1, 2, figsize=(W_FULL, 2.45), gridspec_kw=dict(width_ratios=[1.0, 1.15], wspace=0.55))
    yrs = [2022, 2023, 2024, 2025, 2026]
    doms = ["Manipulation", "Humanoid", "Mobile manipulation", "Navigation"]
    series = [(d, [sum(1 for m in D if year(m) == y and macro_domain(m) == d) for y in yrs]) for d in doms]
    tot = stacked_bars(a, yrs, series, SLOT[:4])
    a.set_xticks(range(len(yrs)), ["2022", "2023", "2024", "2025", "2026*"])
    for i, t in enumerate(tot):
        a.text(i, t + 1.5, f"{int(t)}", ha="center", va="bottom", fontsize=7.2, color=INK2)
    a.set_ylabel("Models"); a.set_ylim(0, 100); grid(a)
    a.legend(loc="upper left", fontsize=6.8, handlelength=1.0, handleheight=0.8, borderaxespad=0.1)
    a.set_title("Models per release year and domain", loc="left")
    panel(a, "a")
    secs = ["Academic", "Mixed", "Industry"]
    keys = [("예", "Open"), ("일부", "Partially open"), ("아니오", "Closed"), ("미확인", "Unverified")]
    cols = [SLOT[0], "#86b6ef", SLOT[1], GRAY_LIGHT]
    series = [(lab, [sum(1 for m in D if sector(m) == s and m["open"] == k) for s in secs]) for k, lab in keys]
    n = [sum(1 for m in D if sector(m) == s) for s in secs]
    stacked_bars(b, secs, series, cols, horizontal=True, pct=True, width=0.6)
    b.set_yticks(range(3), [f"{s}\n(n = {k})" for s, k in zip(secs, n)])
    b.invert_yaxis(); b.set_xlim(0, 100); b.set_xlabel("Share of models (%)"); grid(b, "x")
    b.legend(loc="upper center", bbox_to_anchor=(0.45, -0.32), ncol=4, fontsize=6.8, handlelength=1.0, columnspacing=0.9)
    b.set_title("Weight availability by developer sector", loc="left")
    panel(b, "b")
    save(fig, "fig2_composition")


# ---------------------------------------------------------------- Fig 3 architecture trends
HEAD_FOLD = [("Discrete / latent tokens", {"이산 토큰", "잠재 액션"}), ("Flow matching", {"flow matching"}), ("Diffusion", {"diffusion"}),
             ("Regression / CVAE", {"회귀", "CVAE"}), ("RL policy", {"RL 정책"}), ("Hybrid / world model / other", {"하이브리드", "영상 world model", "기타"}),
             ("Not disclosed", {"미공개"})]
FAM_FOLD = [("Qwen", {"Qwen"}), ("Llama", {"Llama"}), ("Gemma", {"Gemma"}), ("Gemini / PaLI-PaLM", {"Gemini", "PaLI·PaLM"}),
            ("Other LM", {"SmolLM", "InternLM", "Phi", "Mamba", "기타"}), ("No LM backbone", {"없음"}), ("Not disclosed", {"미공개"})]


def yb(m):
    return max(2023, year(m))


def fig_architecture():
    fig, (a, b) = plt.subplots(1, 2, figsize=(W_FULL, 3.4), gridspec_kw=dict(wspace=0.25))
    yrs = [2023, 2024, 2025, 2026]
    lab = ["2022–23", "2024", "2025", "2026*"]
    series = [(l, [sum(1 for m in D if yb(m) == y and m["hk"] in ks) for y in yrs]) for l, ks in HEAD_FOLD]
    cols = SLOT[:6] + [GRAY_LIGHT]
    tot = stacked_bars(a, yrs, series, cols, pct=True, width=0.62)
    a.set_xticks(range(4), [f"{l}\n(n = {int(t)})" for l, t in zip(lab, tot)])
    a.set_ylim(0, 100); a.set_ylabel("Share of models (%)"); grid(a)
    a.set_title("Action-head family (all models)", loc="left"); panel(a, "a")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.6, handlelength=1.0, columnspacing=0.8)
    vla = [m for m in D if m["type"] == "VLA"]
    series = [(l, [sum(1 for m in vla if yb(m) == y and m["fam"] in ks) for y in yrs]) for l, ks in FAM_FOLD]
    cols = SLOT[:5] + [GRAY_DARK, GRAY_LIGHT]
    tot = stacked_bars(b, yrs, series, cols, pct=True, width=0.62)
    b.set_xticks(range(4), [f"{l}\n(n = {int(t)})" for l, t in zip(lab, tot)])
    b.set_ylim(0, 100); grid(b)
    b.set_title("Language-model backbone (VLA models)", loc="left"); panel(b, "b")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.6, handlelength=1.0, columnspacing=0.8)
    save(fig, "fig3_architecture")


# ---------------------------------------------------------------- Fig 4 model size over time
def dnum(m):
    mo = re.match(r"(\d{4})-(\d{2})", m["date"])
    return int(mo.group(1)) + (int(mo.group(2)) - 0.5) / 12 if mo else None


def short(name):
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


def fig_size():
    fig, ax = plt.subplots(figsize=(W_TEXT, 3.2))
    types = [("VLA", "VLA"), ("VA", "VA (no pretrained VLM)"), ("기타", "Other (world model, controller, planner)")]
    for (t, lab), col in zip(types, SLOT[:3]):
        pts = [(dnum(m), m["pb"]) for m in D if m["type"] == t and m["pb"] and dnum(m)]
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=16, color=col, edgecolor="white", linewidth=0.6, label=f"{lab} (n = {len(pts)})", zorder=3)
    import statistics as S
    for y in [2023, 2024, 2025, 2026]:
        v = [m["pb"] for m in D if m["pb"] and max(2023, year(m)) == y]
        x0, x1 = (2022.75, 2024.0) if y == 2023 else (y, y + 1 if y < 2026 else 2026.8)
        ax.plot([x0 + 0.06, x1 - 0.06], [S.median(v)] * 2, color=INK, linewidth=1.2, zorder=4)
    ax.set_yscale("log"); ax.set_ylim(0.001, 200)
    ax.set_yticks([0.001, 0.01, 0.1, 1, 10, 100], ["1M", "10M", "100M", "1B", "10B", "100B"])
    ax.set_xlim(2022.7, 2026.85); ax.set_xticks([2023, 2024, 2025, 2026], ["2023", "2024", "2025", "2026"])
    ax.set_ylabel("Total parameters (log scale)"); ax.set_xlabel("Release date")
    grid(ax, "both")
    for mid, dx, dy, ha in [("rt-2", 0.0, 1.5, "center"), ("divla", 0.05, 1.0, "left"), ("dreamzero", 0.06, 1.0, "left"), ("challenging-terrain-transformer", 0.06, 1.0, "left")]:
        m = BYID[mid]
        ax.annotate(short(m["name"]), (dnum(m), m["pb"]), xytext=(dnum(m) + dx, m["pb"] * dy), fontsize=6.6, color=INK2, ha=ha, va="bottom" if dy > 1 else "center")
    h, l = ax.get_legend_handles_labels()
    h.append(Line2D([], [], color=INK, linewidth=1.2)); l.append("Yearly median (2022 pooled with 2023)")
    ax.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=6.8, handletextpad=0.4, columnspacing=1.2)
    save(fig, "fig4_size")


# ---------------------------------------------------------------- Fig 5 training compute
ACC_FOLD = [("Hopper (H100/H800/H200)", r"H100|H800|H200|MI300"), ("A100 / A800", r"A100|A800"), ("Blackwell (GB200)", r"GB200"), ("TPU", r"TPU"),
            ("V100", r"V100"), ("Workstation / consumer GPU", r"RTX|A4000|A5000|A6000|L40|A40|A10"), ("Not disclosed", r".*")]


def acc_fold(a):
    for lab, rx in ACC_FOLD:
        if re.search(rx, a):
            return lab


def fig_training():
    fig, (a, b) = plt.subplots(1, 2, figsize=(W_FULL, 4.6), gridspec_kw=dict(width_ratios=[1.0, 1.05], wspace=0.75))
    rows = sorted([(m["gpuh"], m) for m in D if m["gpuh"] is not None], key=lambda x: x[0])
    secs = ["Academic", "Mixed", "Industry"]
    for i, (g, m) in enumerate(rows):
        s = sector(m)
        a.plot([1, g], [i, i], color=GRID, linewidth=0.8, zorder=1)
        a.scatter([g], [i], s=18, color=SLOT[secs.index(s)] if s in secs else GRAY_DARK, edgecolor="white", linewidth=0.6, zorder=3)
    a.set_yticks(range(len(rows)), [short(m["name"]) for _, m in rows], fontsize=6.2)
    a.set_xscale("log"); a.set_xlim(10, 1e5); a.set_ylim(-0.8, len(rows) - 0.2)
    a.set_xlabel("Training compute (GPU/TPU-hours, log scale)"); grid(a, "x")
    a.legend(handles=[Line2D([], [], marker="o", linestyle="", color=c, markersize=4.5, label=s) for s, c in zip(secs, SLOT)],
             loc="lower right", fontsize=6.8, handletextpad=0.2, borderaxespad=0.2)
    a.set_title(f"Reported compute ({len(rows)} of {len(D)} models)", loc="left"); panel(a, "a")
    stages = [("사전학습", "Pretraining"), ("사후학습", "Post-training"), ("파인튜닝", "Fine-tuning"), ("과제별 학습", "Per-task training"), ("시뮬 RL", "Simulation RL")]
    recs = [r for rs in TG.values() for r in rs]
    series = [(lab, [sum(1 for r in recs if r["st"] == s and acc_fold(r["acc"]) == lab) for s, _ in stages]) for lab, _ in ACC_FOLD]
    tot = stacked_bars(b, [l for _, l in stages], series, SLOT[:6] + [GRAY_LIGHT], horizontal=True, width=0.6)
    b.set_yticks(range(len(stages)), [f"{l}\n(n = {int(t)})" for (_, l), t in zip(stages, tot)])
    b.invert_yaxis(); b.set_xlabel("Training records"); grid(b, "x")
    b.legend(loc="upper center", bbox_to_anchor=(0.42, -0.13), ncol=2, fontsize=6.6, handlelength=1.0, columnspacing=0.8)
    b.set_title("Accelerator family by training stage", loc="left"); panel(b, "b")
    save(fig, "fig5_training")


# ---------------------------------------------------------------- Fig 6 disclosure heatmap
def fig_disclosure():
    st = json.load(open("../data/stats.json"))
    items = st["disclosure_items"]
    cols = [("Academic", st["disclosure_by_sector"]["Academic"]), ("Mixed", st["disclosure_by_sector"]["Mixed"]),
            ("Industry", st["disclosure_by_sector"]["Industry"]), ("All", dict(st["disclosure_overall"], _n=st["n_models"]))]
    import numpy as np
    M = np.array([[100 * c[k] / c["_n"] for _, c in cols] for k in items])
    fig, ax = plt.subplots(figsize=(W_TEXT * 0.82, 3.6))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f4f8fe"] + BLUE_RAMP[1::2] + ["#0d366b"])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=7.2, color="white" if M[i, j] >= 55 else INK)
    ax.set_xticks(range(len(cols)), [f"{l}\n(n = {c['_n']})" for l, c in cols])
    ax.set_yticks(range(len(items)), items)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True); ax.set_yticks([y - 0.5 for y in range(1, len(items))], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6); ax.tick_params(which="minor", length=0)
    ax.axvline(2.5, color="white", linewidth=4)
    ax.xaxis.tick_top()
    ax.set_title("Share of models disclosing each item (%)", loc="left", pad=26)
    save(fig, "fig6_disclosure")


# ---------------------------------------------------------------- Fig 7 estimator validation
def fig_estimator():
    cal = json.load(open("../data/calibration.json"))
    fig, (a, b) = plt.subplots(1, 2, figsize=(W_FULL, 3.4), gridspec_kw=dict(width_ratios=[1.0, 1.0], wspace=0.62))
    tiers = [("Embedded (Jetson)", {"임베디드"}), ("Desktop / workstation GPU", {"데스크톱", "워크스테이션", "노트북"}), ("Data-centre GPU", {"데이터센터"})]
    import numpy as np
    xs = np.logspace(0, 4, 50)
    a.fill_between(xs, xs / 2, xs * 2, color="#f0efec", linewidth=0, zorder=0, label="Within 2×")
    a.plot(xs, xs, color=MUTED, linewidth=0.8, zorder=1)
    for (lab, ts), col in zip(tiers, SLOT[:3]):
        pts = [p for p in cal["per_anchor"] if p["tier"] in ts]
        a.scatter([p["measured_ms"] for p in pts], [p["predicted_ms"] for p in pts], s=20, color=col, edgecolor="white", linewidth=0.6, zorder=3, label=f"{lab} (n = {len(pts)})")
    names = {p["model"]: short(BYID[p["model"]]["name"]) for p in cal["per_anchor"]}
    # hand-placed labels for the five largest errors (text position in data coordinates, thin leader line)
    place = {("turbovla", "rtx-4090"): (60, 4.2, "left"), ("tinyvla", "rtx-a6000"): (10, 260, "left"), ("spatialvla", "rtx-4090"): (10, 600, "left"),
             ("rdt-1b", "rtx-4090"): (230, 17, "left"), ("pi0", "jetson-agx-orin-64"): (700, 140, "left")}
    devshort = {"rtx-4090": "RTX 4090", "rtx-a6000": "RTX A6000", "jetson-agx-orin-64": "AGX Orin"}
    for p in cal["per_anchor"]:
        k = (p["model"], p["device"])
        if k in place:
            tx, ty, ha = place[k]
            a.annotate(f"{names[p['model']]} ({devshort[p['device']]})", (p["measured_ms"], p["predicted_ms"]), xytext=(tx, ty), textcoords="data",
                       fontsize=6.0, color=INK2, ha=ha, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.5, shrinkA=1, shrinkB=3))
    a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(8, 3000); a.set_ylim(3, 3000)
    a.set_xlabel("Measured latency per inference (ms)"); a.set_ylabel("Estimated latency (ms)")
    grid(a, "both"); a.set_aspect("equal", adjustable="box")
    a.legend(loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=2, fontsize=6.3, handletextpad=0.3, columnspacing=0.8, labelspacing=0.3)
    a.set_title(f"Estimate vs. measurement ({cal['current']['n']} anchors)", loc="left"); panel(a, "a")
    ab = cal["ablation"]
    bars = [("Memory-bound only", ab["memory_only"]["calibrated"]), ("Compute-bound only", ab["compute_only"]["calibrated"]),
            ("Single-pass roofline", ab["single_pass"]["calibrated"]), ("Structured, peak specs", cal["nominal"]),
            ("Structured, calibrated", cal["current"]), ("Structured, leave-one-out", cal["loo"]), ("Cross-device transfer*", cal["transfer"])]
    y = list(range(len(bars)))
    vals = [v["median_x"] for _, v in bars]
    cols = [GRAY_DARK] * 4 + [SLOT[0]] * 2 + [SLOT[0]]
    b.barh(y, vals, color=cols, height=0.58, edgecolor="white", linewidth=0.8)
    for i, (lab, v) in enumerate(bars):
        b.text(v["median_x"] * 1.06, i, f"{v['median_x']:.2f}×  ({v['within2']}/{v['n']} within 2×)", va="center", fontsize=6.5, color=INK2)
    b.set_yticks(y, [l for l, _ in bars]); b.invert_yaxis()
    b.set_xscale("log"); b.set_xlim(1, 60); b.set_xticks([1, 2, 5, 10, 20], ["1×", "2×", "5×", "10×", "20×"])
    b.set_xlabel("Median fold error (log scale)"); grid(b, "x")
    b.set_title("Estimator variants (lower is better)", loc="left"); panel(b, "b")
    save(fig, "fig7_estimator")


# ---------------------------------------------------------------- Fig 8 deployability
def fig_deploy():
    st = json.load(open("../data/stats.json"))
    devs = st["deploy_devices"]
    import numpy as np
    precs = [(2, "bf16"), (1, "int8"), (0.5, "int4")]
    fig, ax = plt.subplots(figsize=(W_FULL, 2.6))
    x = np.arange(len(devs)); w = 0.26
    judged = None
    for k, ((b, lab), col) in enumerate(zip(precs, SLOT[:3])):
        v = [st["deploy"][f"{d['id']}|{b:g}|10"].get("ok", 0) if f"{d['id']}|{b:g}|10" in st["deploy"] else st["deploy"][f"{d['id']}|{b}|10"].get("ok", 0) for d in devs]
        ax.bar(x + (k - 1) * w, v, width=w * 0.92, color=col, edgecolor="white", linewidth=0.6, label=lab)
    j = st["deploy"][f"{devs[0]['id']}|2|10"]
    judged = sum(v for kk, v in j.items() if kk != "na")
    ax.axhline(judged, color=MUTED, linewidth=0.8)
    ax.text(len(devs) - 0.5, judged + 2, f"models with enough size information to judge ({judged})", ha="right", va="bottom", fontsize=6.6, color=INK2)
    LBL = {"jetson-orin-nano-super": "Jetson\nOrin Nano S.", "jetson-orin-nx-16": "Jetson\nOrin NX", "jetson-agx-orin-64": "Jetson\nAGX Orin",
           "jetson-agx-thor": "Jetson\nAGX Thor", "rtx-4060-laptop": "RTX 4060\nLaptop", "rtx-4090-laptop": "RTX 4090\nLaptop", "rtx-4090": "RTX\n4090",
           "rtx-5090": "RTX\n5090", "rtx-pro-6000": "RTX PRO\n6000", "a100-80": "A100\nSXM", "h100-sxm": "H100\nSXM"}
    ax.set_xticks(x, [f"{LBL[d['id']]}\n{d['mem']:g} GB" for d in devs], fontsize=6.5)
    ax.set_ylabel("Models at ≥10 Hz that fit in memory"); ax.set_ylim(0, 140); grid(ax)
    ax.legend(loc="upper left", ncol=3, fontsize=6.8, handlelength=1.0)
    save(fig, "fig8_deploy")


# ---------------------------------------------------------------- Fig 9 RL and base control
RL_FOLD = [("VLA RL post-training", {"VLA RL 사후학습"}), ("RL-trained controller", {"RL 제어기 학습"}), ("RL low-level controller under VLA", {"RL 하위 제어기 결합"}),
           ("RL-generated data", {"RL 데이터 활용"}), ("Reward / preference / value learning", {"보상·선호 최적화", "가치 학습·계획"}),
           ("No RL", {"미사용"}), ("Not disclosed", {"미공개"})]
BASE_FOLD = [("Direct base velocity / pose", {"베이스 속도·자세 직접 출력"}), ("Waypoints → tracking controller", {"웨이포인트 → 추종 제어기"}),
             ("Discrete motion actions", {"이산 이동 행동"}), ("Commands / latents → RL locomotion", {"명령·잠재 → RL 보행 제어기"}),
             ("RL policy drives joints", {"RL 정책이 직접 구동"}), ("Whole-body joints / planning", {"전신 관절·자세 직접 출력", "계획·최적화로 이동 결정"}),
             ("Format not stated", {"형식 미기재"})]


def fig_rl_base():
    fig, (a, b) = plt.subplots(2, 1, figsize=(W_FULL * 0.86, 4.5), gridspec_kw=dict(hspace=0.95))
    doms = ["Manipulation", "Humanoid", "Mobile manipulation", "Navigation"]
    series = [(l, [sum(1 for m in D if macro_domain(m) == d and m["rlcat"] in ks) for d in doms]) for l, ks in RL_FOLD]
    tot = stacked_bars(a, doms, series, SLOT[:5] + [GRAY_LIGHT, GRAY_DARK], horizontal=True, pct=True, width=0.62)
    a.set_yticks(range(4), [f"{d} (n = {int(t)})" for d, t in zip(doms, tot)]); a.invert_yaxis()
    a.set_xlim(0, 100); a.set_xlabel("Share of models (%)"); grid(a, "x")
    a.legend(loc="upper center", bbox_to_anchor=(0.4, -0.3), ncol=4, fontsize=6.5, handlelength=1.0, columnspacing=0.8)
    a.set_title("Where reinforcement learning enters the pipeline", loc="left"); panel(a, "a")
    kinds = [("바퀴형", "Wheeled"), ("사족보행", "Quadruped"), ("휴머노이드 보행", "Legged humanoid"), ("비행", "Aerial"), ("시뮬 전용", "Simulation only")]
    mob = [m for m in D if any(t != "고정" for t in m["base"]["types"])]
    series = [(l, [sum(1 for m in mob if k in m["base"]["types"] and m["base"]["cat"] in ks) for k, _ in kinds]) for l, ks in BASE_FOLD]
    tot = stacked_bars(b, [l for _, l in kinds], series, SLOT[:6] + [GRAY_LIGHT], horizontal=True, width=0.62)
    b.set_yticks(range(len(kinds)), [f"{l} (n = {int(t)})" for (_, l), t in zip(kinds, tot)]); b.invert_yaxis()
    b.set_xlabel("Models (a model may list several base types)"); grid(b, "x")
    b.legend(loc="upper center", bbox_to_anchor=(0.4, -0.3), ncol=4, fontsize=6.5, handlelength=1.0, columnspacing=0.8)
    b.set_title("How the policy commands the mobile base", loc="left"); panel(b, "b")
    save(fig, "fig9_rl_base")


if __name__ == "__main__":
    fig_composition(); fig_architecture(); fig_size(); fig_training(); fig_disclosure(); fig_estimator(); fig_deploy(); fig_rl_base()
    print("ok")
