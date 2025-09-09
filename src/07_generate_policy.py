# -*- coding: utf-8 -*-
"""
07_generate_policy.py
Convert extractions.jsonl → policies.json + rules_readable.md
Usage:
  python src/07_generate_policy.py --in outputs/extractions.jsonl --out-json outputs/policies.json --out-md outputs/rules_readable.md
"""
import argparse, json, os

def to_policy(rec):
    effect = "permit"
    if rec.get("clause_type") == "DENY":
        effect = "deny"
    elif rec.get("clause_type") == "OBLIG":
        effect = "oblig"

    subj = rec.get("subject", [])
    act = rec.get("action", [])
    obj = rec.get("object", [])
    cond = rec.get("condition", [])
    excp = rec.get("exception", [])

    policy = {
        "policy_id": rec["id"],
        "effect": effect,
        "subject": [{"attr":"role","op":"in","value":subj}] if subj else [],
        "action": act,
        "resource": [{"attr":"data_category","op":"in","value":obj}] if obj else [],
        "condition": [{"attr":"consent","op":"=","value": True}] if ("经同意" in "".join(cond)) else [],
        "exception": [{"attr":"law_enforcement_request","op":"=","value": True}] if ("依法要求" in "".join(excp)) else [],
        "provenance": rec.get("provenance", {}),
        "explain": f"{'、'.join(subj) if subj else '主体'}{ '不得' if effect=='deny' else '可以' }{ '、'.join(act) if act else '相关动作' }{' '}{ ' '.join(obj) if obj else '' }"
    }
    return policy

def to_md(rec, policy):
    lines = []
    lines.append(f"[{rec.get('article_no','未知条款')}]")
    lines.append(f"规则类型：{rec.get('clause_type')}")
    lines.append(f"规则：{policy['explain']}")
    if policy["condition"]:
        lines.append("前置条件：已取得个人信息主体同意（经同意）")
    if policy["exception"]:
        lines.append("例外：法律法规另有规定/依法要求")
    prov = policy.get("provenance",{})
    lines.append(f"出处：{prov.get('doc','?')} {prov.get('article','?')} 偏移 {prov.get('offset','?')}")
    return "\n".join(lines) + "\n\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out-json", dest="out_json", required=True)
    ap.add_argument("--out-md", dest="out_md", required=True)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    policies = []
    md = []
    with open(args.inp, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            pol = to_policy(rec)
            policies.append(pol)
            md.append(to_md(rec, pol))

    with open(args.out_json, "w", encoding="utf-8") as w:
        json.dump(policies, w, ensure_ascii=False, indent=2)
    with open(args.out_md, "w", encoding="utf-8") as w:
        w.write("".join(md))

    print(f"[OK] Wrote {len(policies)} policies → {args.out_json}")
    print(f"[OK] Wrote readable rules → {args.out_md}")

if __name__ == "__main__":
    main()
