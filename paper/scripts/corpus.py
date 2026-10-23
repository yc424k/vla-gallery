"""Shared helpers: load the gallery corpus and derive analysis variables."""
import json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = json.load(open(os.path.join(ROOT, "gallery", "data.json")))
TG = json.load(open(os.path.join(ROOT, "gallery", "train_gpu.json")))
EN = json.load(open(os.path.join(ROOT, "i18n", "en.json")))
HF = json.load(open(os.path.join(ROOT, "gallery", "hf.json")))


def en(s):
    return EN.get(s, s)


def year(m):
    return int(m["date"][:4])


def macro_domain(m):
    """The curated group decides first; models in time-based groups fall back to domain keywords."""
    g, dom = m["group"], m["domain"]
    if g == "내비게이션":
        return "Navigation"
    if g == "모바일 매니퓰레이션":
        return "Mobile manipulation"
    if "내비게이션" in dom or "VLN" in dom:
        return "Navigation"
    if "모바일" in dom or "사족보행" in dom:
        return "Mobile manipulation"
    if "휴머노이드" in dom:
        return "Humanoid"
    return "Manipulation"


COMPANY = ["Google", "DeepMind", "Everyday Robots", "Meta", "Microsoft", "NVIDIA", "ByteDance", "Alibaba", "AMAP", "Tencent",
           "Huawei", "Xiaomi", "Toyota", "Physical Intelligence", "Figure", "Tesla", "1X", "Boston Dynamics", "Covariant", "Skild",
           "Dyna", "Generalist", "Galaxea", "GigaAI", "Unitree", "AgiBot", "Agibot", "Galbot", "Midea", "SenseTime", "Hugging Face",
           "valeo", "Lambda", "Hello Robot", "Horizon Robotics", "Robbyant", "Ant Group", "Spirit AI", "BeingBeyond", "Light Origins",
           "Qwen Team", "X Square", "Xspark", "Sunday", "Dexterity", "Apple", "Noematrix", "PsiBot", "WorldEngine", "Differential Robotics",
           "BMW", "Westlake Robotics", "AI²Robotics", "Hupan Lab", "IBM", "Intern Robotics"]
# Public, university or non-profit research institutes that contain no company keyword are academic by default.
NOT_COMPANY = ["Shanghai AI Lab", "Intern Robotics"]  # Intern Robotics is the Shanghai AI Laboratory team name


def sector(m):
    org = m["org"]
    if org.startswith("미확인"):
        return "Unknown"
    if "Open X-Embodiment" in org:
        return "Mixed"
    parts = [p.strip() for p in re.split(r"[;·,+]| 외|\band\b", re.sub(r"\(.*?\)", "", org)) if p.strip()]
    comp = []
    for p in parts:
        is_c = any(k in p for k in COMPANY) and not any(k in p for k in NOT_COMPANY)
        if "PKU-PsiBot Joint Lab" in p:
            is_c = False
        comp.append(is_c)
    if all(comp):
        return "Industry"
    if not any(comp):
        return "Academic"
    return "Mixed"


def disclosed_text(v):
    """True when a free-text field carries a value (not undisclosed / unverified / not applicable)."""
    if v is None:
        return False
    s = str(v).strip()
    return bool(s) and not s.startswith(("미공개", "미확인", "해당 없음", "확인불가"))


def na_text(v):
    return v is not None and str(v).strip().startswith("해당 없음")


def hz_value(m):
    """Lowest number followed by Hz in the control-rate field (the policy/action rate), else None."""
    s = m["hz"]
    if s.startswith("미공개"):
        return None
    nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:–\s*\d+(?:\.\d+)?\s*)?(?:Hz|fps|FPS)", s)]
    return nums[0] if nums else None


HEAD_ORDER = ["이산 토큰", "잠재 액션", "flow matching", "diffusion", "하이브리드", "회귀", "CVAE", "RL 정책", "영상 world model", "기타", "미공개"]
FAM_ORDER = ["Qwen", "Llama", "Gemma", "Gemini", "PaLI·PaLM", "SmolLM", "InternLM", "Phi", "Mamba", "기타", "없음", "미공개"]


def weights_open(m):
    """Weights released (fully or partly). Records marked 'unverified' count as released when hf.json lists an
    official Hugging Face weight repository for them (six models)."""
    return m["open"] in ("예", "일부") or (m["open"] == "미확인" and bool(HF.get(m["id"])))


def chunk_kind(m):
    s = m["chunk"]
    if s.startswith(("미공개", "미확인", "미기재")):
        return "undisclosed"
    if s.startswith("없음"):
        return "none"
    return "chunked"


ACC_FAMILIES = ["Hopper (H100/H800/H200)", "A100 / A800", "Blackwell (GB200)", "TPU", "V100", "Other data-centre GPU (L40, L40S, A40, A10)",
                "Workstation / consumer GPU (RTX)", "Not disclosed"]


def acc_family(a):
    if "TPU" in a:
        return "TPU"
    if re.search(r"GB200|B200", a):
        return "Blackwell (GB200)"
    if re.search(r"H100|H800|H200|MI300", a):
        return "Hopper (H100/H800/H200)"
    if re.search(r"A100|A800", a):
        return "A100 / A800"
    if "V100" in a:
        return "V100"
    if re.search(r"\bL40S?\b|\bA40\b|\bA10G?\b", a):
        return "Other data-centre GPU (L40, L40S, A40, A10)"
    if re.search(r"RTX|A4000|A5000|A6000", a):
        return "Workstation / consumer GPU (RTX)"
    return "Not disclosed"
