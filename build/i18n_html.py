"""HTML 쪽(<script>·<style> 밖) 한국어 텍스트 노드와 속성값을 찾거나 번역으로 바꾼다."""
import re
KO = re.compile(r'[가-힣]')
BLOCK = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.S)
TEXT = re.compile(r'>([^<]+)<')
ATTR = re.compile(r'\b(title|placeholder|aria-label|content|label|alt)="([^"]*)"')
def _outside(html, fn):
    out, pos = [], 0
    for m in BLOCK.finditer(html):
        out.append(fn(html[pos:m.start()])); out.append(m.group(0)); pos = m.end()
    out.append(fn(html[pos:])); return "".join(out)
def segments(html):
    segs = []
    def grab(part):
        for m in TEXT.finditer(part):
            t = m.group(1).strip()
            if KO.search(t): segs.append(t)
        for m in ATTR.finditer(part):
            if KO.search(m.group(2)): segs.append(m.group(2))
        return part
    _outside(html, grab); return segs
def translate(html, tr):
    def text(m):
        raw = m.group(1); t = raw.strip()
        if not KO.search(t) or t not in tr: return m.group(0)
        lead = raw[:len(raw) - len(raw.lstrip())]; trail = raw[len(raw.rstrip()):]
        return ">" + lead + tr[t] + trail + "<"
    def attr(m):
        v = m.group(2)
        return m.group(1) + '="' + tr[v].replace('"', "&quot;") + '"' if KO.search(v) and v in tr else m.group(0)
    return _outside(html, lambda part: ATTR.sub(attr, TEXT.sub(text, part)))
