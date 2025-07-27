#!/usr/bin/env python3
"""
process_pdfs.py

High-performance PDF outline extractor using PyMuPDF (fitz).
Reads PDFs from /app/input and outputs JSON files into /app/output.
Groups spans into lines based on bounding-box Y-coordinates for accurate heading capture, supports multilingual text.
"""

import fitz  # PyMuPDF
import json
from pathlib import Path
import unicodedata
from collections import Counter


def has_letter(text: str) -> bool:
    """
    Check if the string contains at least one letter (supports all Unicode scripts).
    """
    return any(unicodedata.category(ch).startswith('L') for ch in text)


def extract_outline(pdf_path: str) -> dict:
    """
    Extract title (topmost line on page1) and hierarchical headings (H1/H2/H3) from PDF.
    """
    doc = fitz.open(pdf_path)
    lines = []  # list of tuples: (page, text, avg_size, avg_y0)

    # 1) Collect and group spans into lines for all pages
    for page_num, page in enumerate(doc, start=1):
        spans = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    txt = span.get("text", "").strip()
                    if not txt or not has_letter(txt):
                        continue
                    x0, y0 = span.get("bbox", (0,0,0,0))[:2]
                    size = round(span.get("size", 0), 1)
                    spans.append({"text": txt, "size": size, "x0": x0, "y0": y0})
        # bucket spans into lines by y-coordinate
        buckets = []
        for s in spans:
            placed = False
            for b in buckets:
                if abs(b[0]["y0"] - s["y0"]) < 2:
                    b.append(s)
                    placed = True
                    break
            if not placed:
                buckets.append([s])
        for b in buckets:
            # sort by x0 and build line text
            b.sort(key=lambda s: s["x0"])
            texts = [s["text"] for s in b]
            if all(len(t)==1 for t in texts) and len(texts) >= 3:
                text = "".join(texts)
            else:
                text = " ".join(texts)
            text = text.strip()
            if not has_letter(text):
                continue
            avg_size = sum(s["size"] for s in b) / len(b)
            avg_y0  = sum(s["y0"] for s in b) / len(b)
            lines.append((page_num, text, round(avg_size,1), avg_y0))

    # 2) Determine title: topmost line on page 1 (smallest y0)
    first_page = [(p, t, sz, y0) for (p, t, sz, y0) in lines if p == 1]
    if first_page:
        # sort by y0 ascending
        top_line = sorted(first_page, key=lambda x: x[3])[0]
        title = top_line[1]
    else:
        title = Path(pdf_path).stem

    # 3) Identify top-3 font sizes for H1, H2, H3
    sizes = sorted({sz for (_, _, sz, _) in lines}, reverse=True)[:3]
    level_map = {sizes[i]: f"H{i+1}" for i in range(len(sizes))}

    # 4) Assemble outline in document order, de-dupe by text
    outline = []
    seen = set()
    for page_num, text, sz, _ in lines:
        lvl = level_map.get(sz)
        if lvl and text not in seen:
            outline.append({"level": lvl, "text": text, "page": page_num})
            seen.add(text)

    return {"title": title, "outline": outline}


def main():
    """
    Process PDFs from /app/input -> write JSON to /app/output.
    """
    inp = Path("/app/input")
    out = Path("/app/output")
    out.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(inp.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in /app/input")
        return

    for pdf in pdfs:
        res = extract_outline(str(pdf))
        out_file = out / f"{pdf.stem}.json"
        out_file.write_text(
            json.dumps(res, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"Processed {pdf.name} -> {out_file.name}")

if __name__ == "__main__":
    main()
