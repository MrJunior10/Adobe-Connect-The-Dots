# Persona‑Driven Document Intelligence (Round 1B)

## Overview

This repository contains a Dockerized solution for **Round 1B: Persona‑Driven Document Intelligence** of the Adobe India Hackathon 2025. Given a collection of PDFs, a persona definition, and a job‑to‑be‑done (specified in `challenge1b_input.json`), the tool extracts and ranks the most relevant sections across documents and provides refined text snippets.

## Approach

1. **PDF Parsing & Line Grouping**

   - Uses **PyMuPDF** to extract text spans along with font size and position.
   - Buckets spans into logical lines by clustering on vertical coordinates.

2. **Heading Detection**

   - Identifies the top‑3 font sizes as candidate heading sizes.
   - Applies strict heuristics: 2–4 Title‑Case words, ≤ 40 chars, no trailing punctuation, split on colons/dashes, Title‑Case normalization.
   - Falls back to size‑based headings if fewer than 5 strict headings are found.

3. **Semantic Ranking**

   - Embeds section titles and the persona+job query using **Sentence‑Transformers (all‑MiniLM‑L6‑v2)**.
   - Ranks sections by cosine similarity.

4. **Diverse Selection**

   - Ensures the top 5 picked sections come from 5 distinct PDFs.

5. **Subsection Refinement**

   - Splits each section’s body into sentences, scores them against the query, and selects the top 3 in document order.
   - Falls back to full page text if a section has no body.

6. **Output**

   - Emits a JSON file named `<challenge_id>.json` (e.g. `round_1b_002.json`) in the `output/` folder with the structure:

   ```json
   {
     "metadata": { /* input docs, persona, job, timestamp */ },
     "extracted_sections": [ /* top‑5 section info */ ],
     "subsection_analysis": [ /* refined_text snippets */ ]
   }
   ```

## Project Structure

```
ADOBE HACKATHON - 1B/
├── input/
│   ├── challenge1b_input.json          # Persona, job, and document list
│   ├── South of France - Cities.pdf
│   ├── South of France - Cuisine.pdf
│   ├── South of France - History.pdf
│   ├── South of France - Restaurants and Hotels.pdf
│   ├── South of France - Things to Do.pdf
│   ├── South of France - Tips and Tricks.pdf
│   └── South of France - Traditions and Culture.pdf
├── output/
│   └── round_1b_002.json               # Generated JSON output
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── round1b_processor_advanced.py       # Main processing script
```

## Requirements

- Python 3.10 (amd64)
- Libraries (in `requirements.txt`):
  - PyMuPDF
  - sentence-transformers
  - torch

All dependencies are installed in the Docker container.

## Build & Run

1. **Build the Docker image** (offline models baked in):

   ```bash
   docker build --platform linux/amd64 -t round1b:advanced .
   ```

2. **Run the container**, mounting your input/output directories:

   ```bash
   docker run --rm \
     -v "$(pwd)/input:/app/input:ro" \
     -v "$(pwd)/output:/app/output" \
     --network none \
     round1b:advanced
   ```

After execution, you’ll find `round_1b_002.json` in the `output/` directory.

## Limitations & Notes

- Heading rules are tuned for these sample PDFs; other documents may require heuristic adjustments.
- Semantic ranking uses a lightweight \~80 MB all‑MiniLM model for fast, offline inference.
- The solution runs fully on CPU and completes within 60 s for up to 10 documents.

---

Happy hacking!

