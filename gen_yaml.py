services = ["book", "clothes", "laptop", "phone", "tablet", "camera", "headphone", "watch", "shoe", "furniture"]
db_template = """
  {name}_db:
    image: postgres:15-alpine
    container_name: {name}_db
    environment:
      POSTGRES_DB: {name}_db
      POSTGRES_USER: {name}_user
      POSTGRES_PASSWORD: {name}_pass
    ports:
      - "{db_port}:5432"
    volumes:
      - {name}_db_data:/var/lib/postgresql/data
    networks:
      - microservices_network
"""

service_template = """
  {name}-service:
    build:
      context: .
      dockerfile: services/{name}_service/Dockerfile
    container_name: {name}-service
    environment:
      - DATABASE_URL=postgresql://{name}_user:{name}_pass@{name}_db:5432/{name}_db
      - RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/
      - SECRET_KEY=your-secret-key-change-in-production
      - DEBUG=True
    ports:
      - "{svc_port}:8000"
    depends_on:
      - {name}_db
      - rabbitmq
    networks:
      - microservices_network
    volumes:
      - ./services/{name}_service:/app
      - ./shared:/shared
    command: python manage.py runserver 0.0.0.0:8000
"""

volumes_template = "  {name}_db_data:\n"

db_output = ""
svc_output = ""
vol_output = ""

for i, s in enumerate(services):
    db_port = 5451 + i
    svc_port = 8021 + i
    db_output += db_template.format(name=s, db_port=db_port)
    svc_output += service_template.format(name=s, svc_port=svc_port)
    vol_output += volumes_template.format(name=s)

print("DB_SECTION")
print(db_output)
print("SVC_SECTION")
print(svc_output)
print("VOL_SECTION")
print(vol_output)
