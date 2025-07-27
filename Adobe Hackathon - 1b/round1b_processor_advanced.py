#!/usr/bin/env python3
"""
round1b_processor_final.py

Round 1B: Persona‑Driven Document Intelligence (Final, with tightened heading heuristics).

- Parallel PDF → sections extraction
- SBERT cosine‑similarity ranking of section titles
- Heuristic heading filtering (2–4 Title‑Case words, ≤40 chars, no trailing punctuation)
- Split headings on colon/dash and take first clause
- Fallback to any size‑based headings if <5 strict
- Ensure 5 distinct documents in final selection
- Sentence‑level scoring with fallback to full page text for refined_text
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz   # PyMuPDF
import unicodedata
from sentence_transformers import SentenceTransformer, util

# ------------- Config -------------
MAX_WORKERS         = 4
TOP_K_SECTIONS      = 5
TOP_K_SENTS         = 3
HEADING_WORDS_MIN   = 2
HEADING_WORDS_MAX   = 4    # tightened from 6 to 4
MAX_HEADING_CHARS   = 40
MODEL_NAME          = "all-MiniLM-L6-v2"
# -----------------------------------

def has_letter(s: str) -> bool:
    return any(unicodedata.category(ch).startswith("L") for ch in s)

def clean_heading(txt: str) -> str:
    # strip trailing punctuation
    t = txt.rstrip(".:;")
    # split on colon/dash and take first clause
    clause = re.split(r"[:\-–]", t, maxsplit=1)[0].strip()
    # title-case each word
    return " ".join(w.capitalize() for w in clause.split())

def extract_sections(pdf_path: Path):
    """
    Extract candidate sections with strict heading heuristics and fallback.
    """
    doc = fitz.open(str(pdf_path))
    spans = []
    for pg, page in enumerate(doc, start=1):
        for blk in page.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln.get("spans", []):
                    txt = sp["text"].strip()
                    if not txt or not has_letter(txt):
                        continue
                    size = round(sp["size"], 1)
                    y0, x0 = sp["bbox"][1], sp["bbox"][0]
                    spans.append((pg, txt, size, y0, x0))
    if not spans:
        return []

    # bucket by y0 into lines
    spans.sort(key=lambda x: x[3])
    lines, bucket = [], [spans[0]]
    for sp in spans[1:]:
        if abs(sp[3] - bucket[-1][3]) < 3:
            bucket.append(sp)
        else:
            lines.append(bucket)
            bucket = [sp]
    lines.append(bucket)

    # collapse buckets to (page, text, size)
    collapsed = []
    for b in lines:
        b.sort(key=lambda x: x[4])
        pg = b[0][0]
        texts = [x[1] for x in b]
        size = round(sum(x[2] for x in b) / len(b), 1)
        txt = "".join(texts) if sum(len(t)==1 for t in texts) > len(texts)//2 else " ".join(texts)
        collapsed.append((pg, txt.strip(), size))

    # determine heading sizes
    top_sizes = sorted({ln[2] for ln in collapsed}, reverse=True)[:3]

    # strict headings
    strict, curr = [], None
    for pg, txt, sz in collapsed:
        words = txt.split()
        is_head = (
            sz in top_sizes
            and HEADING_WORDS_MIN <= len(words) <= HEADING_WORDS_MAX
            and all(w and w[0].isupper() for w in words)
            and len(txt) <= MAX_HEADING_CHARS
            and not txt.endswith(('.', ':', ';'))
        )
        if is_head:
            if curr:
                strict.append(curr)
            curr = {"section_title": txt, "page_number": pg, "content": ""}
        elif curr:
            curr["content"] += txt + " "
    if curr:
        strict.append(curr)

    # fallback if too few
    if len(strict) < TOP_K_SECTIONS:
        fallback, curr = [], None
        for pg, txt, sz in collapsed:
            if sz in top_sizes and len(txt.split()) <= 8:
                if curr:
                    fallback.append(curr)
                curr = {"section_title": txt, "page_number": pg, "content": ""}
            elif curr:
                curr["content"] += txt + " "
        if curr:
            fallback.append(curr)
        # merge and dedupe
        merged, seen = [], set()
        for sec in strict + fallback:
            title = sec["section_title"]
            if title not in seen:
                merged.append(sec)
                seen.add(title)
            if len(merged) >= TOP_K_SECTIONS:
                break
        return merged
    else:
        return strict[:TOP_K_SECTIONS]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir",  required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    inp = Path(args.input_dir)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    spec = json.loads((inp / "challenge1b_input.json").read_text(encoding="utf-8"))
    docs = spec["documents"]
    persona = spec["persona"]["role"]
    job     = spec["job_to_be_done"]["task"]
    cid     = spec["challenge_info"]["challenge_id"]
    query   = f"{persona}. {job}"

    # load embedding model once
    model = SentenceTransformer(MODEL_NAME)

    # 1) extract sections in parallel
    all_secs = []
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        futures = {ex.submit(extract_sections, inp / d["filename"]): d["filename"] for d in docs}
        for fut in as_completed(futures):
            fn = futures[fut]
            for sec in fut.result():
                sec["filename"] = fn
                all_secs.append(sec)

    # 2) embed & rank section titles
    titles = [s["section_title"] for s in all_secs]
    if not titles:
        print("No headings found—exiting.")
        return

    sec_embs = model.encode(titles, convert_to_tensor=True)
    q_emb    = model.encode([query], convert_to_tensor=True)[0]
    sims     = util.cos_sim(q_emb, sec_embs)[0]
    scored   = sorted(
        [{**sec, "score": float(sims[i])} for i, sec in enumerate(all_secs)],
        key=lambda x: x["score"], reverse=True
    )

    # 3) ensure 5 distinct docs and post‑process titles
    final, seen = [], set()
    for s in scored:
        if s["filename"] not in seen:
            # clean up the title
            s["section_title"] = clean_heading(s["section_title"])
            final.append(s)
            seen.add(s["filename"])
        if len(final) == TOP_K_SECTIONS:
            break
    for idx, s in enumerate(final, start=1):
        s["importance_rank"] = idx

    # 4) subsection refinement with fallback
    sub_anal = []
    for sec in final:
        cont = sec["content"].strip()
        if not cont:
            doc  = fitz.open(str(inp / sec["filename"]))
            page = doc.load_page(sec["page_number"] - 1)
            cont = page.get_text().replace("\n", " ").strip()

        sents = re.split(r"(?<=[.!?]) +", cont)
        sents = [s.strip() for s in sents if s.strip()]
        if not sents:
            refined = cont
        else:
            emb_s = model.encode(sents, convert_to_tensor=True)
            sim_s = util.cos_sim(q_emb, emb_s)[0]
            topk  = sim_s.topk(min(TOP_K_SENTS, len(sents)))
            idxs  = topk.indices.cpu().numpy()
            idxs.sort()
            refined = " ".join(sents[i] for i in idxs)

        sub_anal.append({
            "document":     sec["filename"],
            "refined_text": refined,
            "page_number":  sec["page_number"]
        })

    # 5) write output
    metadata = {
        "input_documents": [d["filename"] for d in docs],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.utcnow().isoformat()
    }
    extracted = [
        {
            "document":        s["filename"],
            "section_title":   s["section_title"],
            "importance_rank": s["importance_rank"],
            "page_number":     s["page_number"]
        }
        for s in final
    ]
    output = {
        "metadata":            metadata,
        "extracted_sections":  extracted,
        "subsection_analysis": sub_anal
    }
    (out / f"{cid}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {cid}.json")

if __name__ == "__main__":
    main()
