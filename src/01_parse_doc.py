# -*- coding: utf-8 -*-
"""
01_parse_doc.py
- If input is a .txt, we simply copy the content to "interim/DSLaw.txt"
- If input is a .pdf, we'll try to parse (requires pdfminer.six). If not installed, show a friendly message.
Usage:
  python src/01_parse_doc.py --in data/raw/DSLaw.pdf --out data/interim/DSLaw.txt
  python src/01_parse_doc.py --in data/interim/sample.txt --out data/interim/DSLaw.txt
"""
import argparse, os, sys

def parse_pdf_to_text(pdf_path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
    except Exception as e:
        print("[WARN] pdfminer.six not installed. Please install it or provide a .txt file instead.")
        print("       pip install pdfminer.six")
        raise
    return extract_text(pdf_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input file (.pdf or .txt)")
    ap.add_argument("--out", dest="out", required=True, help="Output TXT path")
    args = ap.parse_args()

    inp = args.inp
    outp = args.out
    os.makedirs(os.path.dirname(outp), exist_ok=True)

    if inp.lower().endswith(".pdf"):
        text = parse_pdf_to_text(inp)
    elif inp.lower().endswith(".txt"):
        with open(inp, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("[ERR] Unsupported input type. Use .pdf or .txt")
        sys.exit(1)

    # simple normalization
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    with open(outp, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[OK] Wrote text to {outp}")

if __name__ == "__main__":
    main()
