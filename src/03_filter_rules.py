# -*- coding: utf-8 -*-
"""
03_filter_rules.py
从 02 的切块输出中过滤“规则性句子”，并保留 02 提供的 article_no 与全文偏移 offset。

使用示例：
  python src/03_filter_rules.py --in data/chunks/chunks.jsonl --out data/candidates/rule_candidates.jsonl
"""

import argparse
import json
import os
import re

# 规则性关键词（可按需扩充）
KEYWORDS = r"(应当|不得|可以|禁止|严禁|需经|经.*(批准|同意|评估)|符合.*条件|.*除外)"
PAT = re.compile(KEYWORDS)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    kept = 0
    with open(args.inp, "r", encoding="utf-8") as f, open(args.out, "w", encoding="utf-8") as w:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            text = obj.get("text", "")
            if PAT.search(text):
                rec = {
                    "doc_id": obj.get("doc_id", "DSLaw"),
                    "article_no": obj.get("article_no", "未知条款"),
                    "text": text,
                    # 这里沿用 02 的全文偏移（内容部分的起止）
                    "offset": obj.get("offset", [0, len(text)])
                }
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                kept += 1

    print(f"[OK] Kept {kept} candidate line(s) → {args.out}")

if __name__ == "__main__":
    main()
