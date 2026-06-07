FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/supplier_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared /shared

# Copy the application code
COPY services/supplier_service /app/

# Expose the port
EXPOSE 8000

# Run migrations and start the server
CMD python wait_for_db.py && python manage.py migrate --noinput && python -u manage.py runserver 0.0.0.0:8000
