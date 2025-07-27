&#x20;&#x20;

# Adobe India Hackathon 2025

Welcome to our submission for the **Adobe India Hackathon 2025**! This repository presents two robust, Dockerized solutions:

* **Round 1A: PDF Outline Extraction**
* **Round 1B: Persona‑Driven Document Intelligence**

Our mission: **Connect what matters—for the user who matters** by transforming static PDFs into structured, persona‑aware insights.

---

## 🏆 Hackathon Theme & Goals

Adobe challenges us to make PDFs **machine‑understandable** and **user‑focused**. We deliver:

* **Automated Structure:** Extract titles and headings without manual intervention.
* **Contextual Relevance:** Surface the most important sections for a given persona and task.
* **Offline Performance:** CPU‑only execution on AMD64, with models <1GB.

---

## 🚀 Architecture Overview

1. **PDF Parsing**  — PyMuPDF/pdfplumber extracts spans with font & position.
2. **Heading Heuristics**  — Clustering and font‑size rules detect titles and headings.
3. **Semantic Embeddings**  — Sentence‑Transformers ranks sections against persona+job queries.
4. **Refinement**  — Sentence‑level scoring ensures concise, contextually relevant snippets.
5. **Containerized**  — Docker images run offline on any AMD64 host.

---

## 📁 Repository Structure

```bash
adobe-hackathon/
├── 1A/                # Round 1A: Outline Extraction
│   ├── input/         # PDFs to process
│   ├── output/        # JSON outlines
│   ├── Dockerfile
│   ├── process_pdfs.py
│   └── requirements.txt

├── 1B/                # Round 1B: Persona Intelligence
│   ├── input/         # challenge1b_input.json + PDFs
│   ├── output/        # Ranked analysis JSON
│   ├── Dockerfile
│   ├── round1b_processor.py
│   └── requirements.txt

└── README.md          # This overview
```

---

## ⚡ Quickstart

### Round 1A: PDF Outline Extraction

```bash
cd 1A
docker build --platform linux/amd64 -t pdf_outline:1a .
docker run --rm \
  -v "$PWD/input:/app/input:ro" \
  -v "$PWD/output:/app/output" \
  --network none \
  pdf_outline:1a
```

### Round 1B: Persona‑Driven Document Intelligence

```bash
cd 1B
docker build --platform linux/amd64 -t doc_intel:1b .
docker run --rm \
  -v "$PWD/input:/app/input:ro" \
  -v "$PWD/output:/app/output" \
  --network none \
  doc_intel:1b
```

Outputs will appear in each `output/` folder respectively.

---

## 🔑 Key Achievements

* **High Precision:** Structured outlines and persona‑aware section ranking.
* **Offline & Scalable:** CPU‑only, AMD64, completing tasks within time limits.
* **Reusable Pipeline:** Modular code easily extends to new PDF layouts and personas.

---

**Thank you for reviewing our submission!**

For questions or live demo requests, feel free to reach out to our team.
