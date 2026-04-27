FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY services/knowledge_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/knowledge_service/ .
COPY data_user500.csv /data_user500.csv

RUN chmod +x start.sh

CMD ["./start.sh"]
