import os
import time
import psycopg2
from urllib.parse import urlparse

def wait_for_db():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not set, skipping wait.")
        return

    url = urlparse(db_url)
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port or 5432

    print(f"⌛ Waiting for database {host}:{port}...")
    
    max_retries = 30
    count = 0
    while count < max_retries:
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            conn.close()
            print("✅ Database is up and running!")
            return
        except psycopg2.OperationalError as e:
            count += 1
            print(f"⚠️ Database not ready yet ({count}/{max_retries}). Retrying in 2s...")
            time.sleep(2)
    
    print("❌ Could not connect to database. Exiting.")
    exit(1)

if __name__ == "__main__":
    wait_for_db()
