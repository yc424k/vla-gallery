"""LaTeX tables generated from the data (../tables/*.tex)."""
import json, math, re
from corpus import D, TG, en, year, macro_domain, sector
from estimator import DEVICES, DEVBY, ANCHORS, BYID, est_latency

KEYS = json.load(open("../data/bibkeys.json"))
CAL = json.load(open("../data/calibration.json"))
ST = json.load(open("../data/stats.json"))
TESTS = json.load(open("../data/disclosure_tests.json"))

NAME_FIX = {
    "π0": r"$\pi_0$", "π0-FAST (FAST 토크나이저)": r"$\pi_0$-FAST", "π0.5": r"$\pi_{0.5}$", "π0.5 + KI (Knowledge Insulation)": r"$\pi_{0.5}$ + KI",
    "Real-Time Chunking (추론시 RTC)": "Real-Time Chunking (inference-time)", "π0.6": r"$\pi_{0.6}$", "π*0.6 (RECAP)": r"$\pi^*_{0.6}$ (RECAP)",
    "학습시 RTC (Training-time RTC, π0.6)": "Training-time RTC", "Atlas LBM (Large Behavior Model on Atlas)": "Atlas LBM",
    "LeVERB (Latent Vision-Language-Encoded Robot Behavior)": "LeVERB", "HAT (Humanoid Policy ~ Human Policy, PH²D)": "HAT",
    "HumanPlus HST (Humanoid Shadowing Transformer)": "HumanPlus HST", "HumanPlus HIT (Humanoid Imitation Transformer)": "HumanPlus HIT",
    "Humanoid Locomotion as Next Token Prediction": "Humanoid Next-Token Locomotion",
    "Challenging-Terrain Transformer (Learning Humanoid Locomotion over Challenging Terrain)": "Challenging-Terrain Transformer",
    "TWIST (Teleoperated Whole-Body Imitation System)": "TWIST", "SONIC (Supersizing Motion Tracking for Natural Humanoid Whole-Body Control)": "SONIC",
    "VIRAL (Visual Sim-to-Real at Scale for Humanoid Loco-Manipulation)": "VIRAL", "Figure RL 보행 제어기 (Reinforcement Learning Walking)": "Figure RL walking controller",
    "1X World Model (1XWM) 정책": "1X World Model policy", "Rho-alpha (ρα)": r"Rho-alpha ($\rho\alpha$)", "Ψ0 (Psi-Zero)": r"$\Psi_0$",
    "π0.7": r"$\pi_{0.7}$", "Galbot AstraBrain(银河星脑) 계열": "Galbot AstraBrain family",
    "Learning Visual Quadrupedal Loco-Manipulation from Demonstrations": "Visual Quadrupedal Loco-Manipulation", "ω-0 (OMEGA-0)": r"$\omega$-0 (OMEGA-0)",
    "τ0-VLA (tau-0)": r"$\tau_0$-VLA",
}


def tname(m):
    n = NAME_FIX.get(m["name"], m["name"])
    n = re.sub(r"\s*\((?![^)]*\$)[^)]{25,}\)", "", n)  # drop long parenthetical descriptions
    return n.replace("&", r"\&").replace("_", r"\_") if "$" not in n else n


def fmt_p(p):
    if p is None:
        return "n/d"
    if p >= 10:
        return f"{p:.0f}"
    if p >= 1:
        return f"{p:.1f}".rstrip("0").rstrip(".")
    return f"{p:.3g}"


DOM = {"Manipulation": "Manip.", "Humanoid": "Hum.", "Mobile manipulation": "MoMa", "Navigation": "Nav."}
TYP = {"VLA": "VLA", "VA": "VA", "기타": "Other"}
FAM = {"없음": "none", "미공개": "n/d", "기타": "other", "PaLI·PaLM": "PaLI/PaLM"}
HEAD = {"이산 토큰": "tokens", "잠재 액션": "latent", "flow matching": "flow", "diffusion": "diffusion", "하이브리드": "hybrid", "회귀": "regression",
        "CVAE": "CVAE", "RL 정책": "RL policy", "영상 world model": "video WM", "기타": "other", "미공개": "n/d"}
OPEN = {"예": "Y", "일부": "P", "아니오": "N", "미확인": "?"}


def models_table():
    rows = sorted(D, key=lambda m: (m["date"][:7], m["name"].lower()))
    out = [r"\begin{longtable}{@{}r p{3.55cm} l l l r l l c r@{}}",
           r"\caption{All 215 models in the corpus, ordered by release month. Domain: Manip.\ = manipulation, Hum.\ = humanoid, MoMa = mobile manipulation, Nav.\ = navigation. Params: total parameters in billions (n/d = not disclosed). LM: language-model family of the backbone. Head: action-head family. W: weights released (Y = yes, P = partially, N = no, ? = unverified). GPU-h: pretraining GPU/TPU-hours where both accelerator count and duration are reported.\label{tab:models}}\\",
           r"\toprule", r"\textbf{\#} & \textbf{Model} & \textbf{Date} & \textbf{Domain} & \textbf{Type} & \textbf{Params} & \textbf{LM} & \textbf{Head} & \textbf{W} & \textbf{GPU-h}\\", r"\midrule", r"\endfirsthead",
           r"\toprule", r"\textbf{\#} & \textbf{Model} & \textbf{Date} & \textbf{Domain} & \textbf{Type} & \textbf{Params} & \textbf{LM} & \textbf{Head} & \textbf{W} & \textbf{GPU-h}\\", r"\midrule", r"\endhead",
           r"\bottomrule", r"\endfoot"]
    for i, m in enumerate(rows, 1):
        g = f"{m['gpuh']:,.0f}" if m["gpuh"] is not None else ""
        out.append(f"{i} & {tname(m)}~\\cite{{{KEYS[m['id']]}}} & {m['date'][:7]} & {DOM[macro_domain(m)]} & {TYP[m['type']]} & {fmt_p(m['pb'])} & "
                   f"{FAM.get(m['fam'], m['fam'])} & {HEAD[m['hk']]} & {OPEN[m['open']]} & {g}\\\\")
    out.append(r"\end{longtable}")
    open("../tables/tab_models.tex", "w").write("\n".join(out) + "\n")


def anchors_table():
    rows = []
    for a in ANCHORS:
        m, dev = BYID[a[0]], DEVBY[a[1]]
        p = est_latency(m, dev, a[2])
        prec = {2.0: "bf16", 1.0: "int8/fp8", 0.5: "int4"}[a[2]]
        ratio = f"{p / a[3]:.2f}" if p else "--"
        rows.append(f"{tname(m)}~\\cite{{{KEYS[m['id']]}}} & {dev['name']} & {prec} & {a[3]:g} & {p:.0f} & {ratio}\\\\" if p else
                    f"{tname(m)}~\\cite{{{KEYS[m['id']]}}} & {dev['name']} & {prec} & {a[3]:g} & -- & --\\\\")
    out = [r"\begin{longtable}{@{}p{3.3cm} p{3.6cm} l r r r@{}}",
           r"\caption{Published latency measurements (anchors) used to calibrate and validate the estimator, with the calibrated estimate. Ratio = estimate/measurement. The video world-model policy (Cosmos Policy) has no estimate because its denoising cost is not modelled.\label{tab:anchors}}\\",
           r"\toprule", r"\textbf{Model} & \textbf{Device} & \textbf{Prec.} & \textbf{Meas. (ms)} & \textbf{Est. (ms)} & \textbf{Ratio}\\", r"\midrule", r"\endfirsthead",
           r"\toprule", r"\textbf{Model} & \textbf{Device} & \textbf{Prec.} & \textbf{Meas. (ms)} & \textbf{Est. (ms)} & \textbf{Ratio}\\", r"\midrule", r"\endhead",
           r"\bottomrule", r"\endfoot"] + rows + [r"\end{longtable}"]
    open("../tables/tab_anchors.tex", "w").write("\n".join(out) + "\n")


TIER = {"임베디드": "Embedded", "노트북": "Laptop", "데스크톱": "Desktop", "워크스테이션": "Workstation", "데이터센터": "Data centre"}


def devices_table():
    out = [r"\begin{table}[H]", r"\caption{Device specifications used by the estimator (memory, memory bandwidth and dense BF16 tensor throughput). Values come from vendor specification pages or are derived from published SM counts and clocks; every value and its derivation is documented in the released dataset.\label{tab:devices}}",
           r"\small", r"\begin{tabularx}{\textwidth}{@{}X l r r r@{}}", r"\toprule",
           r"\textbf{Device} & \textbf{Class} & \textbf{Memory (GB)} & \textbf{Bandwidth (GB/s)} & \textbf{BF16 (TFLOPS)}\\", r"\midrule"]
    for d in DEVICES:
        out.append(f"{d['name']} & {TIER[d['tier']]} & {d['mem_gb']:g} & {d['bw_gbs']:,.0f} & {d['bf16_tflops']:g}\\\\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{table}"]
    open("../tables/tab_devices.tex", "w").write("\n".join(out) + "\n")


def tests_table():
    out = [r"\begin{table}[H]", r"\caption{Disclosure of each item by industry-only models versus all other models (academic-only and mixed teams; two models with unknown affiliation excluded). OR: odds ratio from Fisher's exact test; $p_\text{Holm}$: Holm-adjusted $p$-value over the 12 items.\label{tab:tests}}",
           r"\small", r"\begin{tabularx}{\textwidth}{@{}X r r r r@{}}", r"\toprule",
           r"\textbf{Item} & \textbf{Industry (n = 74)} & \textbf{Other (n = 139)} & \textbf{OR} & $\boldsymbol{p}_\textbf{Holm}$\\", r"\midrule"]
    for r in TESTS:
        p = r["p_holm"]
        ps = "<0.001" if p < 0.001 else f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
        out.append(f"{r['item']} & {r['ind']} ({r['ind_pct']:.0f}\\%) & {r['oth']} ({r['oth_pct']:.0f}\\%) & {r['odds']:.2f} & {ps}\\\\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{table}"]
    open("../tables/tab_tests.tex", "w").write("\n".join(out) + "\n")


def variants_table():
    ab = CAL["ablation"]
    rows = [("Memory-bound only (weights read once)", ab["memory_only"]["calibrated"]), ("Compute-bound only ($2Pn$ FLOPs)", ab["compute_only"]["calibrated"]),
            ("Single-pass roofline, no head structure", ab["single_pass"]["calibrated"]), ("Structured roofline, peak specifications", CAL["nominal"]),
            ("Structured roofline, calibrated (this work)", CAL["current"]), ("Structured roofline, leave-one-out", CAL["loo"]),
            ("Cross-device transfer from a measured anchor", CAL["transfer"])]
    out = [r"\begin{table}[H]", r"\caption{Accuracy of estimator variants on the published latency anchors. Fold error is $\max(\hat L/L, L/\hat L)$; bias is the geometric mean of $\hat L/L$ (values below 1 mean underestimation). The first three variants use the calibrated efficiency constants; ``peak specifications'' uses $\beta=\varphi=\gamma=1$ and no fixed overheads.\label{tab:variants}}",
           r"\small", r"\begin{tabularx}{\textwidth}{@{}X r r r r r@{}}", r"\toprule",
           r"\textbf{Variant} & \textbf{n} & \textbf{Median fold error} & \textbf{$\le$1.5$\times$} & \textbf{$\le$2$\times$} & \textbf{Bias}\\", r"\midrule"]
    for lab, v in rows:
        out.append(f"{lab} & {v['n']} & {v['median_x']:.2f}$\\times$ & {v['within1_5']} & {v['within2']} & {v['bias_gm']:.2f}\\\\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{table}"]
    open("../tables/tab_variants.tex", "w").write("\n".join(out) + "\n")


def tune_table():
    T = ST["tune"]
    cfg = [("rtx-4090|1", "1$\\times$ RTX 4090 (24 GB)"), ("rtx-5090|1", "1$\\times$ RTX 5090 (32 GB)"), ("a100-80|1", "1$\\times$ A100 (80 GB)"),
           ("h100-sxm|8", "8$\\times$ H100 (80 GB)"), ("jetson-agx-thor|1", "Jetson AGX Thor (128 GB)")]
    out = [r"\begin{table}[H]", r"\caption{Estimated fine-tuning feasibility for the " + str(ST["n_open_est"]) + r" open-weight models with enough size information. Each cell gives the number of models whose estimated per-GPU memory fits (90\% of device memory; 75\% on Jetson) and, in parentheses, the largest such model (total parameters). Memory assumes the ``normal'' activation budget (4~GB + 5~GB per billion parameters per GPU). Head-only applies to the models with a separable flow-matching or diffusion head of known size.\label{tab:tune}}",
           r"\small", r"\begin{tabularx}{\textwidth}{@{}X c c c c@{}}", r"\toprule",
           r"\textbf{Configuration} & \textbf{Full} & \textbf{LoRA} & \textbf{QLoRA} & \textbf{Head only}\\", r"\midrule"]
    def cell(k):
        v = T[k]; mp = v.get("max_P")
        return f"{v.get('ok', 0)} ($\\le${fmt_p(mp)}B)" if mp else "0"
    for k, lab in cfg:
        out.append(f"{lab} & " + " & ".join(cell(f"{k}|{m}") for m in ("full", "lora", "qlora", "head")) + r"\\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{table}"]
    open("../tables/tab_tune.tex", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    models_table(); anchors_table(); devices_table(); tests_table(); variants_table(); tune_table()
    print("tables written")
