FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from service directory
COPY services/chatbot_service/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /shared

# Copy service code
COPY services/chatbot_service /app/

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "main.py"]
