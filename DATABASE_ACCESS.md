# 📊 Database Access Guide

## Neo4j Knowledge Graph

### URL
- **Browser**: http://localhost:7474/browser/
- **Direct**: http://localhost:7474

### Authentication
- **Username**: (không cần - đã tắt auth)
- **Password**: (không cần - đã tắt auth)

### Cách sử dụng
1. Mở http://localhost:7474/browser/
2. Đợi 10-15 giây cho Neo4j khởi động
3. Click nút **"Connect"** (không cần nhập user/pass)
4. Nếu hỏi username/password, để trống và click Connect

### Các query thử nghiệm
```cypher
// Xem tất cả products
MATCH (p:Product) RETURN p LIMIT 10

// Xem tất cả customers
MATCH (c:Customer) RETURN c LIMIT 10

// Xem user actions
MATCH (c:Customer)-[r:VIEWED|ADDED_TO_CART|BOUGHT]->(p:Product)
RETURN c, r, p LIMIT 20

// Xem tất cả nodes và relationships
MATCH (n) RETURN n LIMIT 50

// Đếm số lượng
MATCH (n) RETURN labels(n), count(n)
```

---

## Qdrant Vector Database

### URL
- **API**: http://localhost:6333/
- **Health**: http://localhost:6333/healthz

### Cách sử dụng

#### 1. Xem danh sách collections
```bash
curl http://localhost:6333/collections
```

#### 2. Xem thông tin một collection
```bash
curl http://localhost:6333/collections/products
```

#### 3. Search vectors (ví dụ)
```bash
curl -X POST http://localhost:6333/collections/products/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, 0.3, 0.4],
    "limit": 5
  }'
```

#### 4. Xem tất cả points trong collection
```bash
curl -X POST http://localhost:6333/collections/products/points/scroll \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "with_payload": true
  }'
```

---

## RabbitMQ Management

### URL
- **Management UI**: http://localhost:15672/

### Authentication
- **Username**: admin
- **Password**: admin123

---

## PostgreSQL Databases

### Các database và ports

| Database | Port | Username | Password |
|----------|------|----------|----------|
| auth_db | 5432 | auth_user | auth_pass |
| customer_db | 5433 | customer_user | customer_pass |
| product_db | 5434 | product_user | product_pass |
| cart_db | 5435 | cart_user | cart_pass |

### Kết nối với psql
```bash
# Auth DB
psql -h localhost -p 5432 -U auth_user -d auth_db

# Customer DB
psql -h localhost -p 5433 -U customer_user -d customer_db
```

---

## Troubleshooting

### Neo4j không truy cập được
1. Kiểm tra container: `docker ps | grep neo4j`
2. Xem logs: `docker logs neo4j`
3. Đợi thêm 30-60 giây sau khi start

### Qdrant không truy cập được
1. Kiểm tra container: `docker ps | grep qdrant`
2. Xem logs: `docker logs qdrant`
3. Test health: `curl http://localhost:6333/healthz`

### Reset databases
```bash
# Xóa tất cả volumes và start lại
docker-compose down -v
docker-compose up -d
```
