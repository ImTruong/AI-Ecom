# CHƯƠNG 4. KIẾN TRÚC HỆ THỐNG VÀ TRIỂN KHAI (TRUONGSHOP AI-ECOM)

> Tài liệu này mô tả kiến trúc tổng thể của dự án **AI-Ecom (TruongShop)** theo đúng hiện trạng codebase và cấu hình trong `docker-compose.yml`.

---

## 4.1 Kiến trúc tổng thể

### 4.1.1 Mô hình hệ thống
Hệ thống được xây dựng theo kiến trúc **microservices**, trong đó mỗi service là một ứng dụng độc lập (đa số là **Django + DRF**, một số service AI là **FastAPI**).

**Các khối chính trong hệ thống:**

- **API Gateway + Web UI (Django)**
  - `api-gateway` (port host **8000** → container 8000)
  - Vừa đóng vai trò *single entry point* cho API (`/api/*`) vừa serve giao diện web bằng Django templates (`/`, `/cart/`, `/profile/`, ...).

- **Nhóm service nghiệp vụ (Django microservices, DB riêng):**
  - `user-service` (Auth Service) — host **8001**
  - `customer-service` — host **8002**
  - `staff-service` — host **8003**
  - `product-service` — host **8004**
  - `rating-service` — host **8005**
  - `cart-service` — host **8006**
  - `order-service` — host **8007**
  - `payment-service` — host **8008**
  - `voucher-service` — host **8009**
  - `tracking-service` — host **8010**
  - `supplier-service` — host **8011**

- **Nhóm AI/Knowledge services:**
  - `recommendation-service` (FastAPI) — host **8101** (container 8001) — gợi ý dựa trên embedding + vector search (Qdrant)
  - `knowledge-service` (FastAPI) — host **8105** (container 8005) — gợi ý/đường đi dựa trên graph (Neo4j)
  - `chatbot-service` (FastAPI RAG) — host **8012** (container 8000) — chatbot tư vấn + tìm sản phẩm
  - `vector-service` (manual profile) — job đồng bộ vector/embedding sang Qdrant

- **Hạ tầng (Infrastructure):**
  - PostgreSQL cho từng service (database-per-service)
  - RabbitMQ (message broker) + management UI
  - Qdrant (vector database)
  - Neo4j (graph database)

> Tham chiếu hiện trạng triển khai: `quick_start.sh` và `docker-compose.yml`.

### 4.1.2 Nguyên tắc thiết kế
- **Database-per-service:** mỗi service có database riêng (PostgreSQL container riêng + volume riêng).
- **Synchronous giao tiếp qua REST/HTTP** (thường đi qua API Gateway đối với client).
- **Asynchronous giao tiếp qua message broker** (RabbitMQ) cho luồng đồng bộ dữ liệu/đẩy sự kiện.
- **Không truy cập DB service khác** trong các service nghiệp vụ cốt lõi.
  - *Lưu ý:* các service AI/knowledge có thể cần **ingest/đọc dữ liệu** để xây dựng chỉ mục (vector/graph). Ở mức kiến trúc, nên ưu tiên **API/Event** hoặc **read-only ETL** thay vì coupling trực tiếp.

---

## 4.2 System Architecture

### 4.2.1 Overview (EN)
The system, **TRUONGSHOP AI-ECOM**, is a distributed microservice-based e-commerce platform. Each core business capability is implemented as an independent Django REST microservice with its own database. A Django-based API Gateway serves as the single entry point for both Web UI pages and backend APIs.

AI capabilities are provided through FastAPI services, including a recommendation engine backed by Qdrant (vector search), a knowledge service backed by Neo4j (graph reasoning), and a RAG-style chatbot service.

### 4.2.2 Microservice Architecture
**Core domains implemented as services:**
- Identity & access: Auth (`user-service`)
- Customer profile: `customer-service`
- Admin/staff operations: `staff-service`
- Product catalog: `product-service`
- Cart: `cart-service`
- Orders: `order-service`
- Payments: `payment-service`
- Vouchers/discounts: `voucher-service`
- Ratings/reviews: `rating-service`
- Suppliers: `supplier-service`
- Tracking/analytics: `tracking-service`

### 4.2.3 (Django) API Gateway
Gateway là lớp trung gian *single entry point*:
- Render web pages (templates)
- Route/forward request `/api/*` sang đúng microservice
- Áp dụng chính sách chung (timeout/retry cơ bản khi forward)

### 4.2.4 Service Communication
Hệ thống dùng chiến lược hybrid:
- **Synchronous:** RESTful APIs over HTTP (real-time operations)
- **Asynchronous:** RabbitMQ (event-driven workflows), ví dụ đồng bộ customer từ Auth sang Customer

### 4.2.5 Containerization & Deployment
Toàn bộ service được container hóa bằng Docker và chạy orchestration bằng Docker Compose (development). Hệ thống có thể mở rộng sang Kubernetes ở môi trường production.

### 4.2.6 System Structure
Cấu trúc dự án (rút gọn):

```text
AI-Ecom/
├── docker-compose.yml
├── quick_start.sh
├── services/
│   ├── api_gateway/
│   ├── auth_service/
│   ├── customer_service/
│   ├── staff_service/
│   ├── product_service/
│   ├── cart_service/
│   ├── order_service/
│   ├── payment_service/
│   ├── voucher_service/
│   ├── rating_service/
│   ├── supplier_service/
│   ├── tracking_service/
│   ├── recommendation_service/   # FastAPI + Qdrant
│   ├── knowledge_service/         # FastAPI + Neo4j
│   ├── chatbot_service/           # FastAPI RAG
│   └── vector_service/            # manual sync to Qdrant
└── shared/
    ├── jwt_utils/                 # JWTManager, jwt_required
    ├── outbox/                    # outbox + publisher helpers
    └── events/                    # event types
```

### 4.2.7 Design Principles
- **Loose Coupling:** service tương tác qua HTTP hoặc message broker
- **High Cohesion:** mỗi service bao gói 1 miền nghiệp vụ
- **Scalability:** scale độc lập theo service
- **Fault Isolation:** lỗi 1 service giảm ảnh hưởng lan rộng nhờ tách process/container

### 4.2.8 Security Considerations
- JWT-based authentication
- Token verification ở các endpoint cần bảo vệ (decorator `jwt_required`)
- Role-based access (customer / staff / admin)
- Quản lý secret/key bằng biến môi trường (`.env`) thay vì hardcode

### 4.2.9 Discussion
Kiến trúc microservices giúp linh hoạt khi mở rộng và cô lập lỗi, đặc biệt phù hợp khi có thêm lớp AI (vector search, graph reasoning, RAG). Tuy nhiên, chi phí vận hành tăng (nhiều container, nhiều DB, message broker), được giảm thiểu bằng Docker Compose, cơ chế healthcheck và script khởi động tự động.

---

## 4.3 API Gateway (Django)

### 4.3.1 Vai trò
- Entry point cho toàn hệ thống (Web UI + API)
- Routing request đến đúng service
- Thiết lập timeout/retry khi forward request

### 4.3.2 Cấu hình routing (hiện trạng)
Gateway forward dựa trên prefix mapping trong `services/api_gateway/gateway/middleware.py`:

| API Prefix | Service đích (internal) |
|---|---|
| `/api/auth/` | `user-service` (Auth) |
| `/api/customer/` | `customer-service` |
| `/api/products/` | `product-service` |
| `/api/cart/` | `cart-service` |
| `/api/orders/` | `order-service` |
| `/api/payments/` | `payment-service` |
| `/api/vouchers/` | `voucher-service` |
| `/api/ratings/` | `rating-service` |
| `/api/suppliers/` | `supplier-service` |
| `/api/tracking/` | `tracking-service` |
| `/api/recommendations/` | `recommendation-service` |
| `/api/chatbot/` | `chatbot-service` |

Gateway cũng expose health endpoint: `GET /health/`.

### 4.3.3 Web pages (Templates)
Ngoài API, gateway render các trang:
- `/` (homepage)
- `/cart/`, `/checkout/`, `/orders/`
- `/login/`, `/register/`, `/profile/`
- các trang staff: `/staff/dashboard/`, `/staff/orders/`, ...

---

## 4.4 Authentication (JWT)

### 4.4.1 Cài đặt & thư viện
Dự án dùng JWT theo hướng **shared utility** tại `shared/jwt_utils` (dựa trên **PyJWT**), thay vì phụ thuộc `djangorestframework-simplejwt`.

- `JWTManager`: tạo/giải mã/verify token
- `jwt_required`: decorator bảo vệ endpoint, trích `Authorization: Bearer <token>`

### 4.4.2 Cấu hình
Trong `auth_service.settings`:
- `JWT_SECRET_KEY` (lấy từ env hoặc `SECRET_KEY`)
- `JWT_ALGORITHM = HS256`
- `JWT_ACCESS_TOKEN_LIFETIME = 3600` (1 giờ)
- `JWT_REFRESH_TOKEN_LIFETIME = 86400` (24 giờ)

### 4.4.3 API endpoints chính (Auth Service)
Các endpoint quan trọng của Auth service (`/api/auth/...` thông qua gateway):
- `POST /api/auth/customer/register/`
- `POST /api/auth/customer/login/`
- `POST /api/auth/staff/login/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/verify/`

### 4.4.4 Luồng xác thực
1. User đăng ký/đăng nhập → nhận `access_token` + `refresh_token`
2. Client gửi token theo header:

```http
Authorization: Bearer <access_token>
```

3. Các service cần bảo vệ endpoint dùng `@jwt_required(...)` để verify access token.

---

## 4.5 Giao tiếp giữa các Service

### 4.5.1 REST API call (Synchronous)
- Client gọi vào Gateway (`http://localhost:8000/...`)
- Gateway forward sang internal service bằng HTTP
- Khuyến nghị áp dụng:
  - Timeout rõ ràng
  - Retry có giới hạn
  - Tránh forward vòng lặp

Ví dụ (ý tưởng) call sang product-service:

```python
import requests

resp = requests.get(
    "http://product-service:8000/api/products/",
    timeout=5,
)
resp.raise_for_status()
```

### 4.5.2 Event-driven (Asynchronous) với RabbitMQ
Hệ thống sử dụng RabbitMQ cho các luồng đồng bộ dữ liệu theo sự kiện.

**Ví dụ: đồng bộ Customer từ Auth → Customer Service**
- Auth service ghi event vào outbox (transactional)
- Worker `user-publisher` polling outbox và publish vào RabbitMQ
- `customer-consumer` subscribe exchange và cập nhật DB customer-service

Thông tin kỹ thuật (hiện trạng trong code):
- Exchange: `ecommerce_events` (type: `topic`)
- Queue: `customer_service_sync_queue`
- Binding key: `customer.*`

**Best practices áp dụng trong consumer:**
- Retry khi connect (exponential backoff)
- Ack/Nack phù hợp, có thể requeue khi lỗi tạm thời

---

## 4.6 Docker hóa hệ thống

### 4.6.1 Dockerfile
Mỗi service có `Dockerfile` riêng trong `services/<service_name>/Dockerfile`.
- Django services: base Python image + cài requirements + chạy `manage.py runserver` hoặc entrypoint tương đương
- FastAPI services: chạy `uvicorn` (recommendation/knowledge) hoặc `python main.py` (chatbot)

### 4.6.2 docker-compose.yml (mô hình triển khai)
Docker Compose định nghĩa:
- **Nhiều Postgres containers** (mỗi service 1 DB)
- RabbitMQ + Qdrant + Neo4j
- Core services + AI services
- Custom network: `microservices_network`

### 4.6.3 Quy trình khởi chạy (quick_start)
Script `quick_start.sh` tự động:
1. `docker compose up -d --build`
2. Chờ healthcheck user-service
3. Chạy migrations cho các Django service
4. Seed dữ liệu (products, vouchers, roles/users)
5. Build vector index (`vector-service` profile manual)
6. Import knowledge graph vào Neo4j (`knowledge-service importer.py`)

---

## 4.7 Luồng hệ thống (End-to-End)

### 4.7.1 Use case: Mua hàng + gợi ý AI
1. User login (Auth service) → nhận JWT
2. Xem danh sách sản phẩm (Product service)
3. Xem chi tiết sản phẩm (Product) + ghi tracking (Tracking) *(tùy luồng frontend)*
4. Add to cart (Cart service)
5. Checkout → tạo order (Order service)
6. Thanh toán (Payment service)
7. Sau hành vi (view/cart/purchase), hệ thống AI có thể:
   - cập nhật vector/embedding (Qdrant)
   - gợi ý sản phẩm (Recommendation service)
   - reasoning theo graph (Knowledge service)
   - tư vấn hội thoại (Chatbot service)

### 4.7.2 Sequence logic (mô tả)
- Gateway nhận request và forward đến từng service theo prefix
- Order service và Payment service phối hợp để cập nhật trạng thái đơn hàng
- Tracking service ghi nhận hành vi → Recommendation service dùng dữ liệu này để personal hóa gợi ý

---

## 4.8 Triển khai Kubernetes (Optional)
Khi cần production-grade orchestration có thể chuyển sang Kubernetes.

Ví dụ Deployment (rút gọn):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
        - name: api-gateway
          image: truongshop/api-gateway:latest
          ports:
            - containerPort: 8000
```

---

## 4.9 Logging và Monitoring
- Logging:
  - Docker logs theo container (`docker compose logs -f <service>`)
  - RabbitMQ logs + management UI (host `15672`)
- Monitoring (gợi ý mở rộng):
  - Prometheus + Grafana
  - Tracing (OpenTelemetry)
  - Centralized logging (ELK/EFK)

---

## 4.10 Đánh giá hệ thống

### 4.10.1 Hiệu năng
- Response time theo từng service
- Throughput theo domain (product/search/order/payment)
- Tối ưu điểm nóng: gateway forwarding, DB query, AI inference (embedding/search)

### 4.10.2 Khả năng mở rộng
- Scale độc lập:
  - gateway + product-service khi traffic duyệt sản phẩm tăng
  - recommendation-service khi tải gợi ý tăng

### 4.10.3 Ưu điểm
- Linh hoạt, dễ mở rộng domain và AI layer
- Cô lập lỗi theo service

### 4.10.4 Nhược điểm
- Phức tạp triển khai/vận hành (nhiều container + DB)
- Debug cross-service khó hơn, cần tracing/centralized logging

---

## 4.11 Bài tập thực hành
- Chạy toàn hệ thống bằng Docker Compose
- Test JWT login + gọi các API cần auth
- Test full flow mua hàng: product → cart → order → payment
- Test AI:
  - build vector index (vector-service)
  - gọi recommendation-service
  - thử chatbot-service với các câu hỏi tìm/mua sản phẩm

---

## 4.12 Checklist đánh giá
- [ ] API Gateway chạy tại `http://localhost:8000`
- [ ] Auth JWT hoạt động: login → token → verify
- [ ] Các service core chạy độc lập và có DB riêng
- [ ] RabbitMQ hoạt động và consumer/publisher chạy được (nếu bật)
- [ ] Docker Compose chạy được + migrations + seed thành công
- [ ] AI stack chạy được: Qdrant + vector index + recommendation/chatbot
- [ ] End-to-end flow: order → payment → tracking/recommendation
