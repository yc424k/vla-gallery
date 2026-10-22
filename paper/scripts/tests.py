"""Fisher exact tests: disclosure rate of industry-only models vs. all other models (Holm-corrected)."""
import json
from scipy.stats import fisher_exact
st = json.load(open("../data/stats.json"))
bs = st["disclosure_by_sector"]
ind = bs["Industry"]; oth = {k: bs["Academic"][k] + bs["Mixed"][k] for k in bs["Academic"]}
rows = []
for k in st["disclosure_items"]:
    a, n1 = ind[k], ind["_n"]; b, n2 = oth[k], oth["_n"]
    odds, p = fisher_exact([[a, n1 - a], [b, n2 - b]])
    rows.append(dict(item=k, ind=a, ind_n=n1, ind_pct=100 * a / n1, oth=b, oth_n=n2, oth_pct=100 * b / n2, odds=odds, p=p))
# Holm step-down
order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
m = len(rows); prev = 0
for rank, i in enumerate(order):
    adj = min(1.0, max(prev, (m - rank) * rows[i]["p"])); rows[i]["p_holm"] = adj; prev = adj
json.dump(rows, open("../data/disclosure_tests.json", "w"), indent=1)
for r in rows:
    print(f'{r["item"]:22s} ind {r["ind"]:3d}/{r["ind_n"]} ({r["ind_pct"]:4.1f}%)  other {r["oth"]:3d}/{r["oth_n"]} ({r["oth_pct"]:4.1f}%)  OR={r["odds"]:.2f} p={r["p"]:.2g} holm={r["p_holm"]:.2g}')
