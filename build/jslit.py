"""JS 소스에서 문자열 리터럴 위치를 찾는다(주석·정규식은 건너뜀)."""
import re
KO = re.compile(r'[가-힣]')
def literals(src):
    out = []; i = 0; n = len(src); prev = ""  # prev: 직전의 의미 있는 문자
    while i < n:
        c = src[i]
        if c in " \t\r\n": i += 1; continue
        if src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j; continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        if c in "\"'`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append((i, j + 1, c)); i = j + 1; prev = c; continue
        if c == "/" and (prev == "" or prev in "(,=:[!&|?{};+" or src[max(0,i-6):i].endswith("return")):
            j = i + 1; cls = False
            while j < n:
                if src[j] == "\\": j += 2; continue
                if src[j] == "[": cls = True
                elif src[j] == "]": cls = False
                elif src[j] == "/" and not cls: break
                elif src[j] == "\n": break
                j += 1
            i = j + 1
            while i < n and src[i].isalpha(): i += 1
            prev = "/"; continue
        prev = c; i += 1
    return out
