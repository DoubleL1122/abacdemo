# -*- coding: utf-8 -*-
import json

path = "data/labeled/clauses_labeled.jsonl"
bad = 0
with open(path, "r", encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        try:
            obj = json.loads(line)
        except Exception as e:
            print(f"[JSON ERR] line {ln}: {e}")
            bad += 1
            continue
        text = obj.get("text","")
        L = len(text)
        for sp in obj.get("spans", []):
            s, e = sp.get("start", -1), sp.get("end", -1)
            if not (0 <= s < e <= L):
                print(f"[SPAN OOB] line {ln} id={obj.get('id')} len={L} span={sp} text={text}")
                bad += 1

print(f"Done. Problem spans: {bad}")
