# CHƯƠNG 4. XÂY DỰNG HỆ THỐNG HOÀN CHỈNH

## 4.1 Kiến trúc tổng thể

### 4.1.1 Mô hình hệ thống

Hệ thống **TruongShop AI-Ecom** được xây dựng theo kiến trúc microservices. Mỗi service là một ứng dụng độc lập, phần lớn được triển khai bằng Django, riêng nhóm AI được triển khai bằng FastAPI/Python để phù hợp với các thư viện học máy, vector database và graph database.

API Gateway được triển khai bằng một Django project riêng. Gateway đóng vai trò điểm vào duy nhất cho giao diện web và các API public. Các request từ client đi vào `api-gateway`, sau đó được route đến service tương ứng thông qua REST API nội bộ trong Docker network.

Các thành phần chính của hệ thống gồm:

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| `api-gateway` | Django | Render Web UI và định tuyến request `/api/*` |
| `user-service` | Django | Đăng ký, đăng nhập, JWT, customer, staff, admin, RBAC, địa chỉ |
| `product-service` | Django | Quản lý danh mục, sản phẩm, loại sản phẩm, biến thể và tồn kho |
| `cart-service` | Django | Quản lý giỏ hàng |
| `order-service` | Django | Tạo đơn hàng, quản lý trạng thái đơn và tracking vận chuyển trong đơn |
| `payment-service` | Django | Quản lý phương thức thanh toán, payment record và payment log |
| `voucher-service` | Django | Quản lý và kiểm tra mã giảm giá |
| `rating-service` | Django | Quản lý đánh giá sản phẩm |
| `supplier-service` | Django | Quản lý nhà cung cấp |
| `tracking-service` | Django REST Framework | Ghi nhận hành vi xem sản phẩm, thêm giỏ, mua hàng |
| `recommendation-service` | FastAPI/Python | Gợi ý cá nhân hóa bằng Qdrant, Neo4j và GRU |
| `recommendation-search-service` | Python HTTP server | Tìm kiếm ngữ nghĩa sản phẩm qua Qdrant |
| `knowledge-service` | FastAPI/Python | Đồng bộ và truy vấn Knowledge Graph Neo4j |
| `chatbot-service` | FastAPI/Python | Chatbot tư vấn theo Dynamic RAG |
| `vector-service` | Python job | Đồng bộ embedding sản phẩm sang Qdrant |

Sơ đồ tổng thể:

```plantuml
@startuml
title Hình 4.1: Microservice architecture of TruongShop AI-Ecom

skinparam componentStyle rectangle
skinparam shadowing false
skinparam defaultFontName Arial

actor "Customer" as Customer
actor "Staff/Admin" as Staff

package "Client Layer" {
  [Web Browser] as Browser
}

package "Gateway Layer" {
  [api-gateway\nDjango] as Gateway
}

package "Business Services\nDjango" {
  [user-service] as User
  [product-service] as Product
  [cart-service] as Cart
  [order-service] as Order
  [payment-service] as Payment
  [voucher-service] as Voucher
  [rating-service] as Rating
  [supplier-service] as Supplier
  [tracking-service] as Tracking
}

package "AI Services\nFastAPI/Python" {
  [recommendation-service] as Rec
  [recommendation-search-service] as Search
  [knowledge-service] as Knowledge
  [chatbot-service] as Chatbot
  [vector-service] as Vector
}

database "PostgreSQL\nDatabase per service" as PG
database "Qdrant\nVector DB" as Qdrant
database "Neo4j\nGraph DB" as Neo4j
queue "RabbitMQ" as RabbitMQ

Customer --> Browser
Staff --> Browser
Browser --> Gateway

Gateway --> User
Gateway --> Product
Gateway --> Cart
Gateway --> Order
Gateway --> Payment
Gateway --> Voucher
Gateway --> Rating
Gateway --> Supplier
Gateway --> Tracking
Gateway --> Rec
Gateway --> Search
Gateway --> Chatbot

User --> PG
Product --> PG
Cart --> PG
Order --> PG
Payment --> PG
Voucher --> PG
Rating --> PG
Supplier --> PG
Tracking --> PG
Chatbot --> PG

User --> RabbitMQ
Rec --> Search
Rec --> Neo4j
Search --> Qdrant
Vector --> Qdrant
Knowledge --> Neo4j
Chatbot --> Search
Chatbot --> Neo4j

@enduml
```

### 4.1.2 Nguyên tắc

Hệ thống tuân theo các nguyên tắc chính sau:

*   **Mỗi service có database riêng**: `auth_db`, `product_db`, `cart_db`, `order_db`, `payment_db`, `voucher_db`, `rating_db`, `supplier_db`, `tracking_db`, `chatbot_db`.
*   **Giao tiếp qua REST API**: client gọi qua API Gateway, các service gọi nhau bằng HTTP nội bộ trong Docker network.
*   **Không truy cập trực tiếp database của service khác trong nghiệp vụ chính**: service chỉ trao đổi dữ liệu qua API hoặc lưu snapshot cần thiết.
*   **AI service đọc/đồng bộ dữ liệu phục vụ chỉ mục**: `knowledge-service` import dữ liệu sang Neo4j, `vector-service` đồng bộ sản phẩm sang Qdrant.
*   **Có cơ chế bất đồng bộ bằng RabbitMQ/Outbox**: dùng cho event phát sinh từ `user-service`.

---

## 4.2 System Architecture

### 4.2.1 Overview

The proposed system, named **TruongShop AI-Ecom**, is designed as a distributed microservice-based e-commerce platform. The architecture follows modern enterprise design principles, ensuring scalability, maintainability, and fault isolation.

Each core business domain is implemented as an independent Django REST microservice. A Django-based API Gateway is used as the single entry point for web pages and API requests. AI capabilities are implemented as separate Python/FastAPI services to support semantic search, recommendation, knowledge graph, and chatbot features.

### 4.2.2 Microservice Architecture

The system consists of the following core services:

| Service | Responsibility |
|---|---|
| User Service | Handles authentication, authorization, user management, customer profile, staff/admin, RBAC and addresses |
| Product Service | Manages product catalog, categories, product types, product variants and inventory |
| Cart Service | Manages shopping cart and cart items |
| Order Service | Processes customer orders, order lifecycle and shipment tracking records |
| Payment Service | Handles payment records, payment methods and payment logs |
| Voucher Service | Handles discount codes and voucher validation |
| Rating Service | Handles product ratings and reviews |
| Supplier Service | Handles supplier information |
| Tracking Service | Records user behavior such as product view, add-to-cart and purchase |
| AI Services | Provide recommendation, semantic search, graph knowledge and chatbot features |

Each service is independently deployable and maintains its own database, following the database-per-service principle.

### 4.2.3 API Gateway

An API Gateway layer is introduced as the single entry point for all client requests. In this system, the gateway is implemented using **Django middleware**.

The gateway is responsible for:

*   Routing incoming `/api/*` requests to the appropriate microservice.
*   Serving web pages using Django templates.
*   Forwarding request method, headers, body and query parameters.
*   Applying basic timeout and retry when a downstream service is temporarily unavailable.

Authentication is performed inside the services by verifying JWT tokens. The gateway forwards the `Authorization` header so that each protected service can verify the token independently.

### 4.2.4 Service Communication

The system adopts a hybrid communication strategy:

*   **Synchronous communication**: RESTful APIs over HTTP are used for real-time operations, such as reading products, adding cart items, creating orders and validating vouchers.
*   **Asynchronous communication**: RabbitMQ and the Outbox Pattern are used for event-driven workflows. For example, when a customer is registered, `user-service` writes an event to `outbox_messages`, then `user-publisher` publishes it to RabbitMQ.

Example synchronous communication:

```python
import requests

response = requests.get(
    "http://product-service:8000/api/products/",
    timeout=5,
)
```

### 4.2.5 Containerization and Deployment

All services are containerized using Docker. Docker Compose is used for development deployment. All containers are connected through the same Docker network named `microservices_network`.

The system includes:

*   Django service containers.
*   FastAPI/Python AI containers.
*   PostgreSQL containers for each service database.
*   RabbitMQ container.
*   Qdrant container.
*   Neo4j container.

### 4.2.6 System Structure

The source code is organized as follows:

```text
AI-Ecom/
|-- docker-compose.yml
|-- quick_start.sh
|-- services/
|   |-- api_gateway/              # Django Gateway + Web UI
|   |-- auth_service/             # user-service: customer, staff, admin, RBAC
|   |-- product_service/          # product-service: categories, products, variants
|   |-- cart_service/
|   |-- order_service/
|   |-- payment_service/
|   |-- voucher_service/
|   |-- rating_service/
|   |-- supplier_service/
|   |-- tracking_service/
|   |-- recommendation_service/   # FastAPI recommendation
|   |-- vector_service/           # Qdrant indexing and search server
|   |-- knowledge_service/        # Neo4j graph service/importer
|   |-- chatbot_service/          # FastAPI chatbot
|-- shared/
|   |-- jwt_utils/                # Shared JWT logic
|   |-- events/                   # Event definitions
|   |-- outbox/                   # Transactional Outbox
|-- AI/
|   |-- new/
|       |-- GRU_best_model.h5
|       |-- encoders.pkl
```

### 4.2.7 Design Principles

The proposed architecture adheres to the following principles:

*   **Loose Coupling**: services interact through APIs or messaging systems.
*   **High Cohesion**: each service encapsulates one business domain.
*   **Scalability**: services can be scaled independently based on workload.
*   **Fault Isolation**: failure in one service does not stop the whole system.
*   **Database Ownership**: each service owns and manages its own database schema.

### 4.2.8 Security Considerations

Security is enforced through:

*   JWT-based authentication.
*   Service-level token verification using shared JWT utilities.
*   Role-based access control for customer, staff and admin.
*   Protected endpoints using `@jwt_required`.
*   Environment variables for database URLs and secret keys.

### 4.2.9 Discussion

Compared to a monolithic architecture, the microservice design improves flexibility and scalability. Each business function can be developed, tested, deployed and scaled independently. This is especially useful for the AI features because recommendation, semantic search and chatbot services have different runtime requirements from normal Django services.

However, microservices also introduce additional complexity in deployment, debugging and service coordination. In this project, the complexity is reduced by using Docker Compose, a shared Docker network, standard REST communication and reusable shared modules such as `jwt_utils` and `outbox`.

---

## 4.3 API Gateway (Django)

### 4.3.1 Vai trò

API Gateway là entry point cho toàn hệ thống. Trong dự án này, API Gateway được triển khai bằng Django project `services/api_gateway`.

Gateway có các vai trò chính:

*   Nhận request từ browser.
*   Render các trang HTML như homepage, cart, checkout, profile, staff dashboard.
*   Routing request `/api/*` đến đúng microservice.
*   Forward header `Authorization` để service đích tự xác thực JWT.
*   Thiết lập timeout và retry cơ bản.

### 4.3.2 Cấu hình routing

Gateway dùng `RoutingMiddleware` để định tuyến theo URL prefix:

```python
ROUTES = {
    "/api/auth/": "http://user-service:8000",
    "/api/customer/": "http://user-service:8000",
    "/api/staff/": "http://user-service:8000",
    "/api/products/": "http://product-service:8000",
    "/api/cart/": "http://cart-service:8000",
    "/api/orders/": "http://order-service:8000",
    "/api/payments/": "http://payment-service:8000",
    "/api/vouchers/": "http://voucher-service:8000",
    "/api/ratings/": "http://rating-service:8000",
    "/api/suppliers/": "http://supplier-service:8000",
    "/api/tracking/": "http://tracking-service:8000",
    "/api/recommendations/search": "http://recommendation-search-service:8002",
    "/api/recommendations/": "http://recommendation-service:8001",
    "/api/chatbot/": "http://chatbot-service:8000",
}
```

Route `/api/recommendations/search` được đặt trước `/api/recommendations/` để request semantic search đi đúng sang `recommendation-search-service`.

### 4.3.3 Web pages

Gateway cũng render các trang giao diện:

| URL | Chức năng |
|---|---|
| `/` | Trang chủ |
| `/search/` | Tìm kiếm sản phẩm |
| `/product/detail/<id>/` | Chi tiết sản phẩm |
| `/cart/` | Giỏ hàng |
| `/checkout/` | Thanh toán/đặt hàng |
| `/orders/` | Danh sách đơn hàng |
| `/profile/` | Hồ sơ khách hàng |
| `/staff/login/` | Đăng nhập staff/admin |
| `/staff/dashboard/` | Dashboard nhân viên |
| `/staff/products/` | Quản lý sản phẩm |
| `/staff/orders/` | Quản lý đơn hàng |
| `/staff/users/` | Quản lý người dùng |
| `/staff/knowledge/` | Quản lý knowledge base cho chatbot |

---

## 4.4 Authentication (JWT)

### 4.4.1 Cài đặt

Hệ thống sử dụng JWT để xác thực người dùng. Thay vì dùng `djangorestframework-simplejwt`, dự án xây dựng module dùng chung tại:

```text
shared/jwt_utils/
```

Module này dùng thư viện `PyJWT` để tạo, giải mã và xác minh token.

### 4.4.2 Cấu hình

JWT được cấu hình bằng các giá trị:

| Cấu hình | Giá trị |
|---|---|
| `JWT_SECRET_KEY` | Lấy từ environment hoặc `SECRET_KEY` |
| `JWT_ALGORITHM` | `HS256` |
| Access token lifetime | 3600 giây |
| Refresh token lifetime | 86400 giây |

Token payload có dạng:

```json
{
  "user_id": 5,
  "user_type": "customer",
  "email": "client@example.com",
  "type": "access"
}
```

### 4.4.3 Luồng

Luồng xác thực:

1.  User login qua `/api/auth/customer/login/` hoặc `/api/auth/staff/login/`.
2.  `user-service` kiểm tra email/password.
3.  Nếu hợp lệ, service trả về `access_token` và `refresh_token`.
4.  Client gửi token trong header:

```http
Authorization: Bearer <access_token>
```

5.  Các service bảo vệ endpoint bằng decorator `@jwt_required`.
6.  Decorator verify token, kiểm tra `user_type`, sau đó gắn `user_id`, `user_type`, `user_email` vào request.

Các endpoint chính:

| Endpoint | Vai trò |
|---|---|
| `POST /api/auth/customer/register/` | Đăng ký khách hàng |
| `POST /api/auth/customer/login/` | Đăng nhập khách hàng |
| `POST /api/auth/staff/login/` | Đăng nhập staff/admin |
| `POST /api/auth/token/refresh/` | Refresh access token |
| `POST /api/auth/token/verify/` | Verify token |

---

## 4.5 Giao tiếp giữa các Service

### 4.5.1 REST API call

Các service giao tiếp đồng bộ với nhau thông qua REST API. Ví dụ, `order-service` cần lấy giỏ hàng hiện tại của customer trước khi tạo đơn:

```python
import requests

cart_resp = requests.get(
    "http://cart-service:8000/api/cart/",
    headers={"Authorization": request.headers.get("Authorization")},
    timeout=5,
)
```

Một số luồng REST quan trọng:

| Service gọi | Service nhận | Mục đích |
|---|---|---|
| `api-gateway` | tất cả service | Forward public API |
| `order-service` | `cart-service` | Lấy giỏ hàng khi checkout |
| `order-service` | `user-service` | Lấy địa chỉ giao hàng |
| `order-service` | `voucher-service` | Validate mã giảm giá |
| `order-service` | `product-service` | Trừ tồn kho |
| `order-service` | `tracking-service` | Ghi nhận purchase |
| `cart-service` | `tracking-service` | Ghi nhận add-to-cart |
| `recommendation-service` | `cart-service`, `order-service`, `tracking-service` | Lấy lịch sử để gợi ý |
| `chatbot-service` | `recommendation-search-service`, Neo4j | Lấy context tư vấn |

### 4.5.2 Message Queue

Hệ thống có RabbitMQ để hỗ trợ giao tiếp bất đồng bộ. Cơ chế hiện tại được triển khai với Transactional Outbox trong `shared/outbox`.

Quy trình:

1.  Service tạo dữ liệu nghiệp vụ.
2.  Event được lưu vào bảng `outbox_messages` cùng transaction.
3.  Worker `user-publisher` đọc event trạng thái `pending`.
4.  Worker publish event sang RabbitMQ exchange `ecommerce_events`.
5.  Nếu publish thành công, event được đánh dấu `published`.
6.  Nếu lỗi, event được retry hoặc đánh dấu `failed`.

### 4.5.3 Best Practice

Các best practice được áp dụng hoặc có thể áp dụng:

*   Set timeout cho REST API call.
*   Retry có giới hạn ở API Gateway.
*   Dùng Outbox để tránh mất event khi publish message.
*   Không gọi vòng lặp giữa các service.
*   Với production, có thể bổ sung circuit breaker và centralized logging.

---

## 4.6 Docker hóa hệ thống

### 4.6.1 Dockerfile

Mỗi service có Dockerfile riêng. Ví dụ một Django service được đóng gói theo hướng:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

Các AI service dùng Dockerfile riêng để cài đặt FastAPI, TensorFlow, SentenceTransformers, Qdrant client hoặc Neo4j driver tùy nhu cầu.

### 4.6.2 docker-compose.yml

Hệ thống được triển khai bằng Docker Compose. Ví dụ rút gọn:

```yaml
services:
  user-service:
    build:
      context: .
      dockerfile: services/auth_service/Dockerfile
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://auth_user:auth_pass@auth_db:5432/auth_db
    depends_on:
      - auth_db
      - rabbitmq
    networks:
      - microservices_network

  product-service:
    build:
      context: .
      dockerfile: services/product_service/Dockerfile
    ports:
      - "8004:8000"
    environment:
      - DATABASE_URL=postgresql://product_user:product_pass@product_db:5432/product_db
    networks:
      - microservices_network

  api-gateway:
    build:
      context: .
      dockerfile: services/api_gateway/Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - user-service
      - product-service
```

Các container chính:

| Container | Host port | Vai trò |
|---|---:|---|
| `api-gateway` | 8000 | Web UI và API Gateway |
| `user-service` | 8001 | Auth/User |
| `product-service` | 8004 | Product catalog |
| `rating-service` | 8005 | Rating |
| `cart-service` | 8006 | Cart |
| `order-service` | 8007 | Order |
| `payment-service` | 8008 | Payment |
| `voucher-service` | 8009 | Voucher |
| `tracking-service` | 8010 | Tracking |
| `supplier-service` | 8011 | Supplier |
| `chatbot-service` | 8012 | Chatbot |
| `recommendation-service` | 8101 | Recommendation |
| `recommendation-search-service` | 8102 | Semantic search |
| `knowledge-service` | 8105 | Neo4j graph service |
| `qdrant` | 6333 | Vector database |
| `neo4j` | 7474, 7687 | Graph database |
| `rabbitmq` | 5672, 15672 | Message broker |

---

## 4.7 Luồng hệ thống (End-to-End)

### 4.7.1 Use case: Mua hàng

Luồng mua hàng trong hệ thống:

1.  User đăng nhập qua `user-service`.
2.  User xem danh sách hoặc chi tiết sản phẩm từ `product-service`.
3.  Hành vi xem sản phẩm được ghi vào `tracking-service`.
4.  User thêm sản phẩm vào giỏ qua `cart-service`.
5.  `cart-service` ghi nhận hành vi add-to-cart sang `tracking-service`.
6.  User tạo đơn hàng qua `order-service`.
7.  `order-service` lấy cart từ `cart-service`.
8.  `order-service` lấy địa chỉ từ `user-service`.
9.  Nếu có voucher, `order-service` gọi `voucher-service` để validate.
10. `order-service` tạo order và order items.
11. `order-service` gọi `product-service` để trừ tồn kho.
12. `order-service` gọi `tracking-service` để ghi purchase.
13. `order-service` gọi `cart-service` để xóa giỏ hàng.
14. User thanh toán qua `payment-service`.
15. User có thể xem trạng thái đơn và tracking vận chuyển trong `order-service`.

### 4.7.2 Sequence logic

```plantuml
@startuml
title End-to-End Purchase Flow

skinparam shadowing false
skinparam sequenceMessageAlign center
skinparam defaultFontName Arial

actor User
participant "api-gateway" as Gateway
participant "user-service" as UserSvc
participant "product-service" as Product
participant "cart-service" as Cart
participant "order-service" as Order
participant "voucher-service" as Voucher
participant "payment-service" as Payment
participant "tracking-service" as Tracking

User -> Gateway: Login
Gateway -> UserSvc: POST /api/auth/customer/login/
UserSvc --> Gateway: JWT tokens
Gateway --> User: Login success

User -> Gateway: View product
Gateway -> Product: GET /api/products/{id}/
Product --> Gateway: Product detail
Gateway -> Tracking: POST /api/tracking/log-view/

User -> Gateway: Add to cart
Gateway -> Cart: POST /api/cart/add/
Cart -> Tracking: POST /api/tracking/add-to-cart/
Cart --> Gateway: Cart updated

User -> Gateway: Place order
Gateway -> Order: POST /api/orders/place/
Order -> Cart: GET /api/cart/
Order -> UserSvc: GET /api/customer/address/
Order -> Voucher: POST /api/vouchers/validate/
Order -> Product: POST /api/products/update-stock/
Order -> Tracking: POST /api/tracking/log-purchase/
Order -> Cart: DELETE /api/cart/clear/
Order --> Gateway: Order created

User -> Gateway: Process payment
Gateway -> Payment: POST /api/payments/process/
Payment --> Gateway: Payment record
Gateway --> User: Checkout result

@enduml
```

### 4.7.3 Use case: Tư vấn và gợi ý AI

Ngoài luồng mua hàng chính, hệ thống có luồng AI để nâng cao trải nghiệm:

1.  Homepage hoặc Cart gọi `/api/recommendations/{user_id}`.
2.  `recommendation-service` lấy cart, order history và tracking history.
3.  Service gọi `recommendation-search-service` để lấy sản phẩm tương đồng trong Qdrant.
4.  Service gọi Neo4j để lấy ứng viên từ graph hành vi.
5.  GRU model re-rank ứng viên nếu model sẵn sàng.
6.  Chat widget gọi `/api/chatbot/ask`.
7.  `chatbot-service` lấy sản phẩm liên quan, lịch sử, voucher và knowledge base để sinh câu trả lời.

---

## 4.8 Đánh giá hệ thống

### 4.8.1 Hiệu năng

Hệ thống tách các miền nghiệp vụ thành nhiều service nên tải được phân tán. Các request đọc sản phẩm đi vào `product-service`, giỏ hàng vào `cart-service`, đơn hàng vào `order-service`, còn tác vụ AI được tách sang service riêng.

Một số yếu tố ảnh hưởng hiệu năng:

*   Response time của API nghiệp vụ phụ thuộc vào PostgreSQL và số lượng service call nội bộ.
*   Response time của recommendation phụ thuộc vào Qdrant, Neo4j và GRU model.
*   Chatbot có thể chậm hơn do cần gọi semantic search, Neo4j, database knowledge base và LLM.

### 4.8.2 Khả năng mở rộng

Kiến trúc microservices cho phép scale từng service:

| Service | Lý do scale |
|---|---|
| `api-gateway` | Nhiều request từ browser |
| `product-service` | Nhiều request xem/tìm sản phẩm |
| `tracking-service` | Nhiều event hành vi |
| `recommendation-service` | Tính toán gợi ý cá nhân hóa |
| `recommendation-search-service` | Tìm kiếm vector |
| `chatbot-service` | Xử lý hội thoại và RAG |

### 4.8.3 Ưu điểm

*   Linh hoạt vì mỗi service có thể phát triển độc lập.
*   Dễ mở rộng theo từng miền nghiệp vụ.
*   Lỗi ở một service ít ảnh hưởng đến toàn hệ thống.
*   Dễ tích hợp AI vì nhóm AI service tách khỏi core business service.
*   Docker Compose giúp triển khai môi trường phát triển nhanh.

### 4.8.4 Nhược điểm

*   Triển khai phức tạp hơn monolith vì có nhiều container và database.
*   Debug khó hơn do request đi qua nhiều service.
*   Cần quản lý tốt network, environment variables và thứ tự khởi động.
*   Cần bổ sung logging tập trung và monitoring nếu triển khai production.

---

## 4.9 Bài tập thực hành

Các phần thực hành có thể kiểm thử trên hệ thống:

*   Triển khai các service bằng Docker Compose.
*   Đăng ký và đăng nhập user bằng JWT.
*   Xem sản phẩm từ `product-service`.
*   Thêm sản phẩm vào giỏ qua `cart-service`.
*   Tạo đơn hàng qua `order-service`.
*   Tạo payment record qua `payment-service`.
*   Kiểm tra dữ liệu tracking sau khi view/add-to-cart/purchase.
*   Chạy `vector-service` để build Qdrant index.
*   Chạy `knowledge-service/importer.py` để build Neo4j graph.
*   Test recommendation và chatbot.

Ví dụ chạy hệ thống:

```bash
./quick_start.sh
```

Ví dụ kiểm tra recommendation:

```bash
curl "http://localhost:8000/api/recommendations/5?limit=10" \
  -H "Authorization: Bearer <access_token>"
```

Ví dụ kiểm tra chatbot:

```bash
curl -X POST "http://localhost:8000/api/chatbot/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "message": "mình muốn mua áo mặc đi chơi, có voucher không?",
    "trigger": "chat"
  }'
```

---

## 4.10 Checklist đánh giá

| Tiêu chí | Trạng thái trong hệ thống |
|---|---|
| Có API Gateway | Có, triển khai bằng Django `api-gateway` |
| Có JWT Auth | Có, dùng `shared/jwt_utils` |
| Có phân quyền | Có, customer/staff/admin và RBAC |
| Có Docker chạy được | Có, qua `docker-compose.yml` và `quick_start.sh` |
| Có database riêng cho service | Có |
| Có REST API giữa service | Có |
| Có flow mua hàng | Có: login → product → cart → order → payment |
| Có AI tư vấn/gợi ý | Có: recommendation, semantic search, chatbot |
| Có vector database | Có, Qdrant |
| Có graph database | Có, Neo4j |
| Có message queue | Có, RabbitMQ |

---

## Kết luận

Microservices phù hợp với hệ thống thương mại điện tử có nhiều miền nghiệp vụ như người dùng, sản phẩm, giỏ hàng, đơn hàng, thanh toán và AI. Trong TruongShop AI-Ecom, mỗi service được tách độc lập, có database riêng và giao tiếp chủ yếu qua REST API.

Kiến trúc này giúp hệ thống linh hoạt, dễ mở rộng và có khả năng cô lập lỗi tốt hơn so với mô hình monolith. Bên cạnh các service nghiệp vụ, hệ thống còn tích hợp các thành phần AI như Qdrant, Neo4j, GRU recommendation và chatbot Dynamic RAG để nâng cao trải nghiệm tìm kiếm, gợi ý và tư vấn mua hàng.
