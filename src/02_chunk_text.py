# -*- coding: utf-8 -*-
"""
02_chunk_text.py
按“行”切块，并从每行起始处解析出条/款号（若有），将其作为 article_no 传给后续步骤。
同时计算去除条/款前缀后的内容在“全文”中的字符偏移 offset=[start, end]。

使用示例：
  python src/02_chunk_text.py --in data/interim/DSLaw.txt --out data/chunks/chunks.jsonl --chunk_size 400 --overlap 60

说明：
- 默认逐行输出（最稳妥，因为法规通常按条/款换行）。如需长文分片，可使用 chunk_size/overlap，
  但当逐行可用时优先逐行（下面的实现就是优先逐行）。
"""

import argparse
import json
import os
import re

# 既支持中文数字也支持阿拉伯数字
ART_PAT = re.compile(
    r"^(?P<a>第[一二三四五六七八九十百千0-9]+条)"
    r"(?:\s*(?P<p>第[一二三四五六七八九十百千0-9]+款))?"
    r"[：:、．.\s]*"
)

def iter_lines_with_offsets(text: str):
    """
    逐行返回： (line_text_without_newline, global_start, global_end_including_line)
    global_* 为该行在全文中的字符下标（基于 Python 字符，非字节）。
    """
    pos = 0
    for raw in text.splitlines(keepends=True):
        line = raw[:-1] if raw.endswith("\n") else raw
        start = pos
        end = start + len(line)
        pos += len(raw)  # 包含换行符
        yield line, start, end

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="输入 TXT 路径")
    ap.add_argument("--out", dest="out", required=True, help="输出 JSONL 路径")
    ap.add_argument("--chunk_size", type=int, default=400, help="可选：长文分片大小（默认逐行）")
    ap.add_argument("--overlap", type=int, default=60, help="可选：分片重叠（仅在长文模式时生效）")
    args = ap.parse_args()

    with open(args.inp, "r", encoding="utf-8") as f:
        full = f.read()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # 逐行处理：为每行解析条/款号；没有新条/款时，沿用上一行解析到的条/款号
    current_article = None
    current_paragraph = None
    out_cnt = 0

    with open(args.out, "w", encoding="utf-8") as w:
        for idx, (line, gstart, gend) in enumerate(iter_lines_with_offsets(full)):
            line_strip = line.strip()
            if not line_strip:
                continue

            m = ART_PAT.match(line_strip)
            removed_prefix_len = 0
            if m:
                current_article = m.group("a")
                current_paragraph = m.group("p")
                # 去掉“第X条 第Y款：”等前缀
                removed_prefix_len = m.end()
                content = line_strip[removed_prefix_len:].strip()
                # 重新计算内容的全文偏移：从行起点 + 前缀长度 + 去除的两边额外空白
                # 先算出行首到内容首的实际字符数
                leading_spaces = len(line) - len(line.lstrip())
                # line_strip = line.lstrip().rstrip()，我们这里只考虑左侧剔除
                # 为了稳妥，直接从行的左侧空白开始算
                content_start_in_line = leading_spaces + removed_prefix_len + (0)
                # 但上面把 line 做了 strip，再计算会混乱——更直观地重新从原行定位：
                # 用原行 line 去掉左侧空白，再在其中找前缀匹配
                l_no_left = line.lstrip()
                left_trim = len(line) - len(l_no_left)
                m2 = ART_PAT.match(l_no_left)
                if m2:
                    content_start_in_line = left_trim + m2.end()
                # 内容起止（全文）
                c_start = gstart + content_start_in_line
                c_end = c_start + len(content)
            else:
                # 没有新条/款号，沿用当前条/款
                content = line_strip
                # 内容（去掉行首空白）的全文偏移
                l_no_left = line.lstrip()
                left_trim = len(line) - len(l_no_left)
                c_start = gstart + left_trim
                c_end = c_start + len(content)

            article_no = None
            if current_article and current_paragraph:
                article_no = f"{current_article} {current_paragraph}"
            elif current_article:
                article_no = current_article

            rec = {
                "doc_id": "DSLaw",
                "idx": idx,
                "article_no": article_no or "未知条款",
                "text": content,
                "offset": [c_start, c_end]  # 内容在“全文”中的字符偏移
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_cnt += 1

    print(f"[OK] Wrote {out_cnt} record(s) → {args.out}")

if __name__ == "__main__":
    main()
