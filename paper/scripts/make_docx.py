"""Convert manuscript.tex into a Word file (../submission/manuscript.docx) with pandoc.
MDPI-specific commands are rewritten into plain LaTeX first; figures use the PNG versions."""
import re, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.abspath(os.path.join(HERE, ".."))
src = open(os.path.join(PAPER, "manuscript.tex"), encoding="utf-8").read()


def arg(text, cmd):
    """Return the balanced-brace argument of the first \\cmd{...} in text."""
    i = text.index("\\" + cmd + "{") + len(cmd) + 2
    depth, j = 1, i
    while depth:
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        j += 1
    return text[i:j - 1]


def replace_cmd(text, cmd, fn):
    while "\\" + cmd + "{" in text:
        start = text.index("\\" + cmd + "{")
        body = arg(text[start:], cmd)
        end = start + len(cmd) + 2 + len(body) + 1
        text = text[:start] + fn(body) + text[end:]
    return text


def strip_comments(t):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in t.split("\n"))


src = strip_comments(src)
title, abstract, keywords, featured = arg(src, "Title"), arg(src, "abstract"), arg(src, "keyword"), arg(src, "featuredapplication")
body = src[src.index("\\begin{document}") + len("\\begin{document}"):src.index("\\reftitle{References}")]
body = body.replace("\\begin{adjustwidth}{-\\extralength}{0cm}", "").replace("\\end{adjustwidth}", "")
for cmd, head in [("authorcontributions", "Author Contributions"), ("funding", "Funding"), ("institutionalreview", "Institutional Review Board Statement"),
                  ("informedconsent", "Informed Consent Statement"), ("dataavailability", "Data Availability Statement"),
                  ("acknowledgments", "Acknowledgments"), ("conflictsofinterest", "Conflicts of Interest")]:
    body = replace_cmd(body, cmd, lambda b, h=head: f"\\section*{{{h}}}\n{b}\n")
body = body.replace("\\abbreviations{Abbreviations}{", "\\section*{Abbreviations}{")
body = re.sub(r"\\appendixtitles\{\w+\}|\\appendixstart|\\appendix\b", "", body)
body = body.replace("\\section[\\appendixname~\\thesection]{", "\\section{Appendix: ")


def inline_inputs(t):
    return re.sub(r"\\input\{(tables/[^}]+)\}", lambda m: open(os.path.join(PAPER, m.group(1) + ".tex"), encoding="utf-8").read(), t)


body = inline_inputs(body)
# Use LaTeX's own numbering (from manuscript.aux) for references and caption prefixes, since pandoc does not number captions
LAB = {}
for m in re.finditer(r"\\newlabel\{([^}@]+)\}\{\{([^}]*)\}", open(os.path.join(PAPER, "manuscript.aux"), encoding="utf-8").read()):
    LAB[m.group(1)] = m.group(2)
body = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(" + LAB.get(m.group(1), "?") + ")", body)
body = re.sub(r"\\ref\{([^}]+)\}", lambda m: LAB.get(m.group(1), "?"), body)


def prefix_captions(t):
    out, pos = [], 0
    for m in re.finditer(r"\\caption\{", t):
        start = m.end()
        depth, j = 1, start
        while depth:
            depth += {"{": 1, "}": -1}.get(t[j], 0)
            j += 1
        cap = t[start:j - 1]
        lab = re.search(r"\\label\{([^}]+)\}", cap)
        if lab and lab.group(1) in LAB:
            kind = "Figure" if lab.group(1).startswith("fig") else "Table"
            out.append(t[pos:start] + f"\\textbf{{{kind} {LAB[lab.group(1)]}.}} ")
            pos = start
    out.append(t[pos:])
    return "".join(out)


body = prefix_captions(body)
body = re.sub(r"\\includegraphics\[[^\]]*\]\{(figures/[^}]+)\}", r"\\includegraphics{\1.png}", body)
body = re.sub(r"\\begin\{tabularx\}\{[^}]*\}\{([^}]*)\}", lambda m: "\\begin{tabular}{" + m.group(1).replace("X", "l") + "}", body)
body = body.replace("\\end{tabularx}", "\\end{tabular}")
body = body.replace("\\vspace{6pt}", "")
# simplify maths that pandoc cannot convert to Word equations
body = body.replace("\\max\\!\\left(", "\\max\\left(").replace(",\\; \\frac", ", \\frac").replace(" \\quad [\\text{ms}]", "\\ \\text{(ms)}")
body = re.sub(r"\\begin\{align\}(.*?)\\end\{align\}",
              lambda m: "\n".join("\\begin{equation}" + ln.replace("&", "").replace("\\\\", "").strip() + "\\end{equation}"
                                   for ln in m.group(1).strip().split("\\\\") if ln.strip()), body, flags=re.S)
macros = open(os.path.join(PAPER, "stats.tex"), encoding="utf-8").read()
doc = (macros + "\n\\begin{document}\n\\title{" + title + "}\n\\author{[Author names and affiliations]}\n\\maketitle\n"
       + "\\section*{Abstract}\n" + abstract + "\n\n\\noindent\\textbf{Keywords:} " + keywords + "\n\n"
       + "\\section*{Featured Application}\n" + featured + "\n" + body + "\n\\section*{References}\n\\end{document}\n")
tmp = os.path.join(PAPER, "submission", "_docx_source.tex")
open(tmp, "w", encoding="utf-8").write(doc)
out = os.path.join(PAPER, "submission", "manuscript.docx")
# citeproc needs ISO dates to print "accessed on"
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
bib = open(os.path.join(PAPER, "references.bib"), encoding="utf-8").read()
bib = re.sub(r"urldate = \{(\d+) (\w+) (\d{4})\}", lambda m: f"urldate = {{{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}}}", bib)
tmpbib = os.path.join(PAPER, "submission", "_docx_refs.bib")
open(tmpbib, "w", encoding="utf-8").write(bib)
subprocess.run(["pandoc", tmp, "-f", "latex", "-t", "docx", "--number-sections", "--citeproc", "--bibliography", tmpbib,
                "--csl", os.path.join(HERE, "mdpi.csl"), "--resource-path", PAPER, "-o", out], check=True, cwd=PAPER)
os.remove(tmp) if not os.environ.get("KEEP") else None
os.remove(tmpbib)
print("wrote", out)
