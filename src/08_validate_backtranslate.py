# -*- coding: utf-8 -*-
"""
08_validate_backtranslate.py
Very simple "back-translation" check: compare key tokens overlap between policy explanation and source text.
Usage:
  python src/08_validate_backtranslate.py --in outputs/policies.json --doc data/interim/DSLaw.txt --out outputs/validation_report.md
"""
import argparse, json, os, re

def tokenize_cn(s):
    # naive: split into characters and filter punctuation
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[，。；：、！？,.!?;:（）()《》<>【】\[\]]", "", s)
    return list(s)

def jaccard(a, b):
    A, B = set(a), set(b)
    if not A and not B: return 1.0
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--doc", dest="doc", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args()

    with open(args.inp, "r", encoding="utf-8") as f:
        policies = json.load(f)
    with open(args.doc, "r", encoding="utf-8") as f:
        source = f.read()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    lines = ["# 验证报告（简版）\n"]
    for p in policies:
        explain = p.get("explain","")
        # locate source sentence by article if possible (demo: use whole source)
        score = jaccard(tokenize_cn(explain), tokenize_cn(source))
        lines.append(f"策略 {p['policy_id']}：回译相似度（Jaccard） = {score:.2f}")
    with open(args.out, "w", encoding="utf-8") as w:
        w.write("\n".join(lines))
    print(f"[OK] Wrote validation report → {args.out}")

if __name__ == "__main__":
    main()
