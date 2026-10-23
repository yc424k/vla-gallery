"""Build ../references.bib: one entry per model (arXiv metadata or the official web source) plus background references.
All arXiv metadata comes from ../data/arxiv_meta.json (fetched with fetch_arxiv.py)."""
import json, re
from corpus import D

META = json.load(open("../data/arxiv_meta.json"))
WEB = json.load(open("../data/web_titles.json"))
NEW = {r["row"]["모델"] for r in json.load(open("../../gallery/new_models.json"))}
LAST4 = {"Xiaomi-Robotics-1", "LingBot-VLA 2.0", "τ0-VLA (tau-0)", "Spark-0"}


def accessed(m):
    if m["name"] in LAST4:
        return "19 October 2026"
    return "14 October 2026" if m["name"] in NEW else "6 October 2026"


GREEK = {"π": r"\pi", "Ψ": r"\Psi", "ψ": r"\psi", "τ": r"\tau", "ω": r"\omega", "ρ": r"\rho", "α": r"\alpha"}


def tex(s):
    """Escape a plain string for BibTeX/LaTeX; keep existing $...$ math, translating Greek letters inside it."""
    parts = re.split(r"(\$[^$]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$") and p.endswith("$") and len(p) > 1:
            for g, c in GREEK.items():
                p = p.replace(g, c + " ")
            out.append(p.replace(" }", "}").replace(" _", "_").replace(" ^", "^").replace(" $", "$"))
            continue
        p = p.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#").replace("_", r"\_")
        p = p.replace("~", r"$\sim$")
        for g, c in GREEK.items():
            p = p.replace(g, "$" + c + "$")
        p = p.replace("∗", "$^*$").replace("—", "---").replace("–", "--").replace("’", "'").replace("‘", "'").replace("“", "``").replace("”", "''")
        p = re.sub(r"[一-鿿]+", "", p)  # drop CJK glyphs (pdfLaTeX); the Latin name is kept
        out.append(p)
    return "".join(out)


CORPORATE = re.compile(r"\b(Team|Collaboration|Contributors|Intelligence)\b|^NVIDIA$")


def bib_authors(names):
    """Clean arXiv author lists: drop punctuation-only entries, brace corporate authors, repair split names."""
    names = [re.sub(r'\s*"[^"]*"\s*', " ", n).strip() for n in names if re.search(r"[A-Za-z]", n)]  # drop quoted nicknames
    out, i = [], 0
    while i < len(names):
        n = names[i]
        if n == "Mojtaba" and i + 1 < len(names) and names[i + 1] == "Komeili":  # arXiv splits this name in two
            n, i = "Mojtaba Komeili", i + 1
        out.append("{" + n + "}" if CORPORATE.search(n) or " " not in n else n)
        i += 1
    return " and ".join(out)


def arxiv_entry(key, aid):
    a = META[aid]
    f = [f"  author = {{{bib_authors(a['authors'])}}}", f"  title = {{{{{tex(a['title'])}}}}}", "  journal = {arXiv}",
         f"  year = {{{a['published'][:4]}}}", f"  volume = {{{{\\normalfont arXiv:{aid}}}}}"]
    if a.get("doi"):
        f.append(f"  doi = {{{a['doi']}}}")
    return f"@article{{{key},\n" + ",\n".join(f) + "\n}\n"


def web_entry(key, author, title, url, date):
    url = url.replace("%", r"\%").replace("#", r"\#")
    return (f"@www{{{key},\n  author = {{{{{tex(author)}}}}},\n  title = {{{{{tex(title)}}}}},\n"
            f"  url = {{{url}}},\n  urldate = {{{date}}}\n}}\n")


ORG_SHORT = {"gemini-robotics-on-device": "Google DeepMind", "gemini-robotics-on-device-2": "Google DeepMind", "gemini-robotics-2": "Google DeepMind",
             "minivla": "Stanford ILIAD", "atlas-lbm": "Boston Dynamics; Toyota Research Institute", "internvla-n1": "Shanghai AI Laboratory",
             "galbot-astrabrain": "Xinhua News Agency", "g0plus": "Galaxea AI", "g0tiny": "Galaxea AI", "go-2": "AgiBot", "act-1": "Sunday Robotics",
             "xiaomi-robotics-1": "Xiaomi", "spirit-v1-5": "Spirit AI", "1x-redwood-ai": "1X Technologies", "1x-world-model": "1X Technologies"}
FALLBACK_TITLE = {"minivla": "MiniVLA (Stanford AI Lab blog post)", "pi0-6": r"$\pi_{0.6}$ Model Card",
                  "rfm-1": "Introducing RFM-1: Giving Robots Human-like Reasoning Capabilities", "unifolm-wma-0": "UnifoLM-WMA-0 (GitHub repository unitreerobotics/unifolm-world-model-action)",
                  "tesla-optimus": "AI & Robotics", "g0plus": "GalaxeaVLA: G0Plus (GitHub repository OpenGalaxea/GalaxeaVLA)",
                  "g0tiny": "GalaxeaVLA: G0Tiny (GitHub repository OpenGalaxea/GalaxeaVLA)", "unifolm-vla-0": "UnifoLM-VLA-0 (GitHub repository unitreerobotics/unifolm-vla)",
                  "gemini-robotics-2": "Gemini Robotics 2: Safety Evaluations", "internvla-n1": "InternVLA-N1: An Open Dual-System Vision-Language Navigation Foundation Model with Learned Latent Plans"}

entries, keymap = [], {}
seen = set()
for m in D:
    p = m["paper"]
    if p.get("id"):
        key = "ax" + p["id"].replace(".", "")
        keymap[m["id"]] = key
        if key not in seen:
            entries.append(arxiv_entry(key, p["id"])); seen.add(key)
        continue
    key = "web-" + m["id"]
    keymap[m["id"]] = key
    if m["id"] == "galbot-astrabrain":
        entries.append(web_entry(key, "Xinhua News Agency", "Galbot AstraBrain report (in Chinese)",
                                 "https://www.xinhuanet.com/digital/20260821/e172222483dc4d75a357145caa74d9d0/c.html", accessed(m)))
        continue
    url = p.get("u") or m["src"]
    title = (FALLBACK_TITLE.get(m["id"]) or WEB.get(m["id"], {}).get("title") or m["name"]).strip()
    title = re.sub(r"\s*[|—–-]\s*(Google DeepMind|Boston Dynamics|1X|DYNA|Generalist AI|Generalist|Sunday Robotics.*|AGIBOT Innovation.*)$", "", title)
    title = re.sub(r"^[\w.-]+/([\w.-]+) · Hugging Face$", r"\1 (Hugging Face model card)", title)
    title = title.replace(" | ", ": ")
    if title.startswith("Page not found") or title in ("", "Access Denied"):
        title = FALLBACK_TITLE.get(m["id"], m["name"])
    entries.append(web_entry(key, ORG_SHORT.get(m["id"], m["org"].split("(")[0].strip()), title, url, accessed(m)))

BACKGROUND = {  # key: arXiv id
    "firoozi2023": "2312.07843", "hu2023toward": "2312.08782", "kawaharazuka2024real": "2402.05741", "ma2024survey": "2405.14093",
    "yao2023bridging": "2312.10807", "adilkhanov2025": "2502.06851", "sapkota2025": "2505.04769", "zhong2025token": "2507.01925",
    "din2025": "2507.10672", "shao2025": "2508.13073", "li2025survey": "2508.15201", "zhang2025pure": "2509.19012",
    "kawaharazuka2025vla": "2510.07077", "guan2025efficient": "2510.17111", "yu2025efficient": "2510.24795", "grover2026edge": "2603.16952",
    "wang2026data": "2604.23001", "sa2026drones": "2607.06706", "lisondra2025": "2505.20503", "shen2026wam": "2606.20781", "lu2026wam": "2609.16074",
    "hu2021lora": "2106.09685", "dettmers2023qlora": "2305.14314", "rajbhandari2020zero": "1910.02054", "zhao2023fsdp": "2304.11277",
    "mitchell2019modelcards": "1810.03993", "gebru2021datasheets": "1803.09010", "strubell2019": "1906.02243", "schwartz2020green": "1907.10597",
    "kaplan2020scaling": "2001.08361", "pope2023inference": "2211.05102", "lipman2023flow": "2210.02747", "ho2020ddpm": "2006.11239",
    "beyer2024paligemma": "2407.07726", "bai2025qwen25vl": "2502.13923", "touvron2023llama2": "2307.09288", "karamcheti2024prismatic": "2402.07865",
    "schulman2017ppo": "1707.06347", "shao2024deepseekmath": "2402.03300", "makoviychuk2021isaacgym": "2108.10470", "lin2024awq": "2306.00978",
    "liu2023libero": "2306.03310", "mees2022calvin": "2112.03227", "li2024simpler": "2405.05941", "sevilla2022compute": "2202.05924",
    "khazatsky2024droid": "2403.12945", "reddi2020mlperf": "1911.02549", "pineau2021reproducibility": "2003.12206", "henderson2020energy": "2002.05651",
    "qi2026humanoidgpt": "2606.03985",
}
bg = []
for k, aid in BACKGROUND.items():
    bg.append(arxiv_entry(k, aid))
for key, author, title, url in [
        ("repo-openpi", "Physical Intelligence", "openpi (official repository of $\\pi_0$ and $\\pi_{0.5}$), README", "https://github.com/Physical-Intelligence/openpi"),
        ("repo-openvla", "Kim, Moo Jin and Pertsch, Karl and others", "OpenVLA (official repository), README", "https://github.com/openvla/openvla"),
        ("repo-go1", "AgiBot World Contributors", "AgiBot World and GO-1 (official repository), README", "https://github.com/OpenDriveLab/AgiBot-World")]:
    bg.append(f"@www{{{key},\n  author = {{{{{author}}}}},\n  title = {{{{{title}}}}},\n  url = {{{url}}},\n  urldate = {{19 October 2026}}\n}}\n"
              if "others" not in author else
              f"@www{{{key},\n  author = {{{author}}},\n  title = {{{{{title}}}}},\n  url = {{{url}}},\n  urldate = {{19 October 2026}}\n}}\n")
bg.append("""@article{williams2009roofline,
  author = {Williams, Samuel and Waterman, Andrew and Patterson, David},
  title = {{Roofline: An Insightful Visual Performance Model for Multicore Architectures}},
  journal = {Commun. ACM},
  year = {2009},
  volume = {52},
  pages = {65--76},
  doi = {10.1145/1498765.1498785}
}
""")
with open("../references.bib", "w") as f:
    f.write("% Auto-generated by scripts/build_bib.py -- model entries from gallery/data.json + arXiv API metadata\n\n")
    f.write("\n".join(bg + entries))
json.dump(keymap, open("../data/bibkeys.json", "w"), indent=1)
print(len(bg), "background +", len(entries), "model entries;", len(keymap), "models mapped")
