# -*- coding: utf-8 -*-
"""
05_train_ner.py
极简NER训练（字符级），输入：data/labeled/clauses_labeled.jsonl
输出：models/bert_ner/
"""
import json, os, torch
from torch.utils.data import Dataset
from transformers import BertTokenizerFast, BertForTokenClassification, Trainer, TrainingArguments

DATA_PATH = "data/labeled/clauses_labeled.jsonl"

class ClauseDataset(Dataset):
    def __init__(self, path, tokenizer, label2id, max_len=128):
        self.samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                text = obj["text"]
                spans = obj.get("spans", [])

                # 字符级标签序列
                labels = ["O"] * len(text)
                L = len(text)
                for sp in spans:
                    s = int(sp.get("start", 0))
                    e = int(sp.get("end", 0))
                    lab = sp.get("label", "O")
                    # 边界修正
                    s = max(0, min(s, L))
                    e = max(0, min(e, L))
                    if e <= s:
                        continue
                    for i in range(s, e):
                        labels[i] = lab

                self.samples.append((text, labels))

        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_len = max_len

    def __len__(self):
        # ⭐️ 一定要有
        return len(self.samples)

    def __getitem__(self, idx):
        text, labels = self.samples[idx]
        # 按字符切分（is_split_into_words=True 让 tokenizer 不合并）
        enc = self.tokenizer(list(text), truncation=True, padding="max_length",
                             max_length=self.max_len, is_split_into_words=True)
        # 标签对齐/截断
        ids = [self.label2id.get(l, 0) for l in labels][:self.max_len]
        ids += [0] * (self.max_len - len(ids))
        enc["labels"] = ids
        return {k: torch.tensor(v) for k, v in enc.items()}

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"训练数据不存在：{DATA_PATH}")
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")
    label_list = ["O", "SUBJECT", "ACTION", "OBJECT", "CONDITION", "EXCEPTION"]
    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for l, i in label2id.items()}

    dataset = ClauseDataset(DATA_PATH, tokenizer, label2id)
    print("样本数量 =", len(dataset))  # ⭐️ 自检
    if len(dataset) == 0:
        raise ValueError("训练集为空：请确认 data/labeled/clauses_labeled.jsonl 里至少有 1 行有效 JSON。")

    model = BertForTokenClassification.from_pretrained(
        "bert-base-chinese",
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id
    )

    args = TrainingArguments(
        output_dir="models/bert_ner",
        per_device_train_batch_size=2,
        num_train_epochs=1,   # 小样本快速演示
        logging_steps=1,
        save_steps=20,
        save_total_limit=1,
        learning_rate=2e-5
    )

    trainer = Trainer(model=model, args=args, train_dataset=dataset)
    trainer.train()
    trainer.save_model("models/bert_ner")
    print("✅ 训练完成，模型已保存到 models/bert_ner")

if __name__ == "__main__":
    main()
