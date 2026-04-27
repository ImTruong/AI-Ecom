FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /shared
COPY services/tracking_service /app/

EXPOSE 8000

CMD python wait_for_db.py && python manage.py migrate --noinput && python -u manage.py runserver 0.0.0.0:8000
