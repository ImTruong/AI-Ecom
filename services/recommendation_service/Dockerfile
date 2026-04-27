FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*
COPY services/recommendation_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/recommendation_service/ .

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
