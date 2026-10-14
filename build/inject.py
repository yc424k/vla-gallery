import json, sys, os
tpl, data, out = sys.argv[1:4]
s = open(tpl, encoding="utf-8").read()
d = json.load(open(data, encoding="utf-8"))
dev_path = os.path.join(os.path.dirname(os.path.abspath(data)), "devices.json")
if "__DEVICES__" in s:
    dv = json.load(open(dev_path, encoding="utf-8"))
    assert s.count("__DEVICES__") == 1
    s = s.replace("__DEVICES__", json.dumps(dv, ensure_ascii=False).replace("</", "<\\/"))
js = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
assert s.count("__DATA__") == 1
open(out, "w", encoding="utf-8").write(s.replace("__DATA__", js))
print(out, len(s.replace("__DATA__", js).encode("utf-8")), "bytes")
