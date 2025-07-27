# Dockerfile
FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# System deps for faiss, PyMuPDF, transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
  && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre‑download SBERT and T5 models (online at build time)
RUN python - <<EOF
from sentence_transformers import SentenceTransformer
from transformers import T5ForConditionalGeneration, T5TokenizerFast
# download SBERT
SentenceTransformer('all-MiniLM-L6-v2')
# download T5
T5ForConditionalGeneration.from_pretrained('t5-small')
T5TokenizerFast.from_pretrained('t5-small')
EOF

# Force offline mode
ENV TRANSFORMERS_OFFLINE=1

# Copy processor script
COPY round1b_processor_advanced.py .

# Default command
CMD ["python", "round1b_processor_advanced.py", "--input-dir", "/app/input", "--output-dir", "/app/output"]
