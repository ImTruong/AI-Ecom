FROM python:3.11-slim

WORKDIR /app

# Copy requirements from service directory
COPY services/recommendation_service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/recommendation_service /app

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
