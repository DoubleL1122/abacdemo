# ABAC Mini Demo (Rule-based Baseline)
本项目是一个可跑通的最小示例：从一条中文“法律条文”生成“人类可读规则 + 策略 JSON”，并做一个简易回译校验。
- 无需训练模型即可运行（使用规则基线）。
- 未来可把 06/07 替换为 BERT 抽取与更复杂的策略生成。

## 目录
(与聊天中的说明一致，略)

## 快速开始（Windows）
1. 安装 Miniconda（若已安装可跳过）。
2. 打开“Anaconda Prompt (miniconda3)”：
   ```bat
   conda create -n abacdemo python=3.10 -y
   conda activate abacdemo
   pip install -r requirements.txt
   ```
3. 运行 Demo（当前仓库根目录）
   ```bat
   python src\02_chunk_text.py --in data\interim\DSLaw.txt --out data\chunks\chunks.jsonl --chunk_size 400 --overlap 60
   python src\03_filter_rules.py --in data\chunks\chunks.jsonl --out data\candidates\rule_candidates.jsonl
   python src\06_predict_extract.py --in data\candidates\rule_candidates.jsonl --terms data\termdict\terms.yaml --out outputs\extractions.jsonl
   python src\07_generate_policy.py --in outputs\extractions.jsonl --out-json outputs\policies.json --out-md outputs\rules_readable.md
   python src\08_validate_backtranslate.py --in outputs\policies.json --doc data\interim\DSLaw.txt --out outputs\validation_report.md
   ```
4. 查看输出：`outputs/` 目录。

## 可选：解析 PDF
准备 `data/raw/DSLaw.pdf` 后：
```bat
pip install pdfminer.six
python src\01_parse_doc.py --in data\raw\DSLaw.pdf --out data\interim\DSLaw.txt
```
