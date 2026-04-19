FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/vector_service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to save time during runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY services/vector_service /app

CMD ["python", "main.py"]
