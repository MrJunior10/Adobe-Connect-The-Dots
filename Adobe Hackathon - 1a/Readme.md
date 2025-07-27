# PDF Outline Extraction (Round 1A)

## Overview

This repository contains a Dockerized solution for **Round 1A: PDF Outline Extraction** of the Adobe India Hackathon 2025. The tool processes up to 50‑page PDF files, extracts the document title and hierarchical headings (H1/H2/H3), and outputs a JSON outline for each PDF.

## Approach

1. **PDF Parsing**

   - Uses **pdfplumber** (or PyMuPDF if preferred) to read each PDF page and extract text spans with font size metadata.

2. **Title Detection**

   - On page 1, selects the text span with the largest font size as the document title.
   - Falls back to the filename if no spans are found.

3. **Heading Identification**

   - Collects all font sizes across the document and picks the top 3 largest as H1, H2, and H3 sizes.
   - Filters spans by those sizes and minimum word count (e.g. ≥ 3 words) to identify headings.

4. **Outline Assembly**

   - Iterates spans in page order, maps font size to heading level (H1/H2/H3), and records the text and page number.
   - Outputs a structured JSON:

   ```json
   {
     "title": "Document Title",
     "outline": [
       { "level": "H1", "text": "First Heading", "page": 1 },
       { "level": "H2", "text": "Subheading",    "page": 2 },
       ...
     ]
   }
   ```

## Project Structure

```
ADOBE HACKATHON - 1A/
├── input/
│   ├── EJ1172284.pdf
│   ├── file01.pdf
│   ├── file02.pdf
│   ├── file03.pdf
│   ├── file04.pdf
│   ├── ML UNIT-1 NOTES.pdf
│   └── নৌকাডুবি-+-রবীন্দ্রনাথ+-ঠাকুর.pdf
├── output/
│   ├── EJ1172284.json
│   ├── file01.json
│   ├── file02.json
│   ├── file03.json
│   ├── file04.json
│   ├── ML UNIT-1 NOTES.json
│   └── নৌকাডুবি-+-রবীন্দ্রনাথ+-ঠাকুর.json
├── sample_outputs/          # Provided ground‑truth JSON examples
├── schema/
│   └── output_schema.json   # JSON schema definition
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── process_pdfs.py          # Main extraction script
```

## Requirements

- **Python 3.10 (amd64)**
- **Libraries** (in `requirements.txt`):
  - pdfplumber (or PyMuPDF)
  - collections
  - pathlib
  - json

All dependencies are installed in the Docker container.

## Docker Build & Run

1. **Build the image** (no GPU, offline compatible):

   ```bash
   docker build --platform linux/amd64 -t pdf_outline:1a .
   ```

2. **Run the container**, mounting input and output:

   ```bash
   docker run --rm \
     -v "$(pwd)/input:/app/input:ro" \
     -v "$(pwd)/output:/app/output" \
     --network none \
     pdf_outline:1a
   ```

Processed JSON files will appear in `output/`, matching the structure defined in `schema/output_schema.json`.

## Performance & Constraints

- **Exec time:** ≤ 10 s for a 50‑page PDF
- **Model size:** N/A (heuristic-based)
- **Offline:** No network calls
- **Runtime:** CPU only, amd64

## Notes

- Heuristic font‑size mapping may require tuning for uncommon PDF layouts.
- The solution is modular to support reuse in Round 1B.

---

Good luck with your submission!
