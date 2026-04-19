FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/vector_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir sentence-transformers && \
    pip install --no-cache-dir -r requirements.txt

COPY services/vector_service/ /app/

CMD ["python", "main.py"]
