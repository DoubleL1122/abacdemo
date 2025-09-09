# -*- coding: utf-8 -*-
"""
06_predict_extract.py  (auto: model first, else rule-based)
- 输入: data/candidates/rule_candidates.jsonl
- 输出: outputs/extractions.jsonl
- 额外: --terms data/termdict/terms.yaml  用于归一化
"""
import argparse, json, os, re, yaml

# ===== 规则基线（兜底） =====
RE_DENY = re.compile(r"(不得|禁止)")
RE_PERMIT = re.compile(r"(可以|得以)")
RE_OBLIG = re.compile(r"(应当|须|需要)")
RE_EXCEPT = re.compile(r"(除外|法律法规另有规定|依法(要求|提出))")

def normalize_by_terms(value:str, alias_map:dict):
    if not value: return value
    for canon, aliases in alias_map.items():
        for a in aliases:
            if a in value:
                return canon
    return value

def rule_based_extract(text:str, terms):
    clause_type = "UNKNOWN"
    if RE_DENY.search(text): clause_type = "DENY"
    elif RE_PERMIT.search(text): clause_type = "PERMIT"
    elif RE_OBLIG.search(text): clause_type = "OBLIG"

    subject = None
    m = re.search(r"([\u4e00-\u9fa5]{2,12})(?:未经|经|在.*下|应当|不得|可以)", text)
    if m: subject = m.group(1)

    action = None
    m = re.search(r"(提供|披露|共享|出示|出境|调取|转让|买卖|处理|公开)", text)
    if m: action = m.group(1)

    obj = None
    m = re.search(r"(个人敏感信息|个人信息|国家秘密|公共数据|数据安全事件|数据)", text)
    if m: obj = m.group(1)

    condition = "经同意" if "同意" in text else None
    exception = "依法要求" if RE_EXCEPT.search(text) else None

    subject = normalize_by_terms(subject, terms.get("subject_alias", {}))
    action  = normalize_by_terms(action , terms.get("action_alias", {}))
    obj     = normalize_by_terms(obj    , terms.get("object_alias", {}))
    if condition:
        condition = normalize_by_terms(condition, terms.get("condition_alias", {}))
    if exception:
        exception = normalize_by_terms(exception, terms.get("exception_alias", {}))

    return {
        "clause_type": clause_type,
        "subject": [subject] if subject else [],
        "action": [action] if action else [],
        "object": [obj] if obj else [],
        "condition": [condition] if condition else [],
        "exception": [exception] if exception else []
    }

# ===== 模型推理（若可用） =====
def try_load_models():
    try:
        from transformers import BertTokenizerFast, BertForTokenClassification, BertForSequenceClassification
        tok = BertTokenizerFast.from_pretrained("bert-base-chinese")
        ner_dir = "models/bert_ner"
        cls_dir = "models/bert_clausecls"
        ner = BertForTokenClassification.from_pretrained(ner_dir)
        cls = BertForSequenceClassification.from_pretrained(cls_dir)
        return tok, ner, cls
    except Exception as e:
        print("[INFO] 模型不可用，使用规则基线。原因：", e)
        return None, None, None

LABELS = ["O", "SUBJECT", "ACTION", "OBJECT", "CONDITION", "EXCEPTION"]
CLS_ID2LAB = {0:"PERMIT", 1:"DENY", 2:"OBLIG", 3:"EXCEPT", 4:"UNKNOWN"}

def model_extract(text, tok, ner, cls, terms):
    import torch
    # 条款类型
    cls_inputs = tok(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        logits = cls(**cls_inputs).logits
        c = int(torch.argmax(logits, dim=-1)[0])
    clause_type = CLS_ID2LAB.get(c, "UNKNOWN")

    # NER（字符级）
    enc = tok(list(text), return_tensors="pt", is_split_into_words=True,
              truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        ner_logits = ner(**enc).logits[0]  # [seq_len, num_labels]
        pred_ids = torch.argmax(ner_logits, dim=-1).tolist()

    # 把连续标签段落成 span，简单合并
    spans_map = {"SUBJECT":[], "ACTION":[], "OBJECT":[], "CONDITION":[], "EXCEPTION":[]}
    cur_lab, cur_start = None, None
    for i, lid in enumerate(pred_ids):
        if i >= len(text): break  # 只取有效字符位置
        lab = LABELS[lid] if lid < len(LABELS) else "O"
        if lab != "O":
            if cur_lab is None:
                cur_lab, cur_start = lab, i
            elif lab != cur_lab:
                spans_map[cur_lab].append(text[cur_start:i])
                cur_lab, cur_start = lab, i
        else:
            if cur_lab is not None:
                spans_map[cur_lab].append(text[cur_start:i])
                cur_lab, cur_start = None, None
    if cur_lab is not None:
        spans_map[cur_lab].append(text[cur_start: min(len(text), 128)])

    # 去重和归一化
    def norm_list(xs, alias):
        out = []
        for x in xs:
            x = x.strip()
            if not x: continue
            canon = normalize_by_terms(x, alias)
            if canon and canon not in out:
                out.append(canon)
        return out

    subject = norm_list(spans_map["SUBJECT"], terms.get("subject_alias", {}))
    action  = norm_list(spans_map["ACTION"] , terms.get("action_alias" , {}))
    obj     = norm_list(spans_map["OBJECT"] , terms.get("object_alias" , {}))
    cond    = norm_list(spans_map["CONDITION"], terms.get("condition_alias", {}))
    excp    = norm_list(spans_map["EXCEPTION"], terms.get("exception_alias", {}))

    return {
        "clause_type": clause_type,
        "subject": subject,
        "action": action,
        "object": obj,
        "condition": cond,
        "exception": excp
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--terms", dest="terms", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args()

    with open(args.terms, "r", encoding="utf-8") as f:
        terms = yaml.safe_load(f)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    tok, ner, cls = try_load_models()
    use_model = all([tok, ner, cls])

    cnt = 0
    with open(args.inp, "r", encoding="utf-8") as f, open(args.out, "w", encoding="utf-8") as w:
        for line in f:
            obj = json.loads(line)
            text = obj["text"]
            if use_model:
                info = model_extract(text, tok, ner, cls, terms)
            else:
                info = rule_based_extract(text, terms)
            rec = {
                "id": f'{obj.get("doc_id","DSLaw")}-cand-{cnt}',
                "article_no": obj.get("article_no"),
                "text": text,
                "provenance": {
                    "doc": "DSLaw.txt",
                    "article": obj.get("article_no"),
                    "offset": obj.get("offset", [0, 0])
                },
                **info
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
            cnt += 1
    print(f"[OK] Wrote {cnt} extraction(s) → {args.out}")

if __name__ == "__main__":
    main()
