"""Fetch arXiv metadata (title, authors, dates, DOI, journal ref) for every arXiv ID used in the paper.
Usage: python3 fetch_arxiv.py id1 id2 ...   (IDs already cached in ../data/arxiv_meta.json are skipped)"""
import json, os, sys, time, urllib.request, xml.etree.ElementTree as ET
CACHE = "../data/arxiv_meta.json"
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
meta = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
want = [i for i in dict.fromkeys(sys.argv[1:]) if i not in meta]
for k in range(0, len(want), 50):
    batch = want[k:k + 50]
    url = "https://export.arxiv.org/api/query?id_list=" + ",".join(batch) + "&max_results=100"
    for attempt in range(4):
        try:
            xml = urllib.request.urlopen(url, timeout=60).read()
            break
        except Exception as e:
            print("retry", attempt, e); time.sleep(2 ** (attempt + 1))
    root = ET.fromstring(xml)
    for e in root.findall("a:entry", NS):
        aid = e.find("a:id", NS).text.rsplit("/abs/", 1)[1]
        base = aid.split("v")[0] if "v" in aid else aid
        meta[base] = dict(id=base, version=aid, title=" ".join(e.find("a:title", NS).text.split()),
                          authors=[a.find("a:name", NS).text for a in e.findall("a:author", NS)],
                          published=e.find("a:published", NS).text[:10], updated=e.find("a:updated", NS).text[:10],
                          doi=(e.find("x:doi", NS).text if e.find("x:doi", NS) is not None else None),
                          journal_ref=(e.find("x:journal_ref", NS).text if e.find("x:journal_ref", NS) is not None else None),
                          summary=" ".join(e.find("a:summary", NS).text.split())[:1500])
    print(f"batch {k // 50 + 1}: {len(batch)} requested, cache now {len(meta)}")
    json.dump(meta, open(CACHE, "w"), indent=1, ensure_ascii=False)
    time.sleep(3.5)
missing = [i for i in sys.argv[1:] if i not in meta]
print("missing:", missing)
