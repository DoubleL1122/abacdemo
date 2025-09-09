# -*- coding: utf-8 -*-
"""
05b_train_clause_cls.py
极简条款类型分类，输入：data/labeled/clauses_labeled.jsonl
输出：models/bert_clausecls/
"""
import json, os, torch
from torch.utils.data import Dataset
from transformers import BertTokenizerFast, BertForSequenceClassification, Trainer, TrainingArguments

DATA_PATH = "data/labeled/clauses_labeled.jsonl"

class ClauseClsDataset(Dataset):
    def __init__(self, path, tokenizer, label2id, max_len=128):
        self.samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                text = obj["text"]
                label = obj.get("clause_type", "UNKNOWN")
                self.samples.append((text, label))
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_len = max_len

    def __len__(self): return len(self.samples)

    def __getitem__(self, idx):
        text, label = self.samples[idx]
        enc = self.tokenizer(text, truncation=True, padding="max_length", max_length=self.max_len)
        enc = {k: torch.tensor(v) for k, v in enc.items()}
        enc["labels"] = torch.tensor(self.label2id.get(label, self.label2id["UNKNOWN"]))
        return enc

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"训练数据不存在：{DATA_PATH}")
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")
    label_list = ["PERMIT","DENY","OBLIG","EXCEPT","UNKNOWN"]
    label2id = {l:i for i,l in enumerate(label_list)}
    id2label = {i:l for l,i in label2id.items()}

    dataset = ClauseClsDataset(DATA_PATH, tokenizer, label2id)
    print("样本数量 =", len(dataset))
    if len(dataset) == 0:
        raise ValueError("训练集为空：请在 data/labeled/clauses_labeled.jsonl 放入至少1行。")

    model = BertForSequenceClassification.from_pretrained(
        "bert-base-chinese",
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id
    )

    args = TrainingArguments(
        output_dir="models/bert_clausecls",
        per_device_train_batch_size=2,
        num_train_epochs=1,
        logging_steps=1,
        save_steps=20,
        save_total_limit=1,
        learning_rate=2e-5
    )

    trainer = Trainer(model=model, args=args, train_dataset=dataset)
    trainer.train()
    trainer.save_model("models/bert_clausecls")
    print("✅ 训练完成，模型已保存到 models/bert_clausecls")

if __name__ == "__main__":
    main()
