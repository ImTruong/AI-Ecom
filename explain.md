# Hướng Dẫn Chi Tiết: Luồng Hoạt Động Của Hệ Thống AI (Qdrant & Neo4j)

Chào bạn! Dưới đây là tài liệu giải thích chi tiết, trực quan và dễ hiểu nhất về cách hệ thống AI trong dự án **TruongShop** hoạt động. Tài liệu này được viết theo dạng sơ đồ và phân tích luồng đi của dữ liệu từ lúc còn là file thô cho đến khi hiển thị kết quả gợi ý ra màn hình cho khách hàng, kèm theo chỉ dẫn chính xác vị trí của từng đoạn code trong dự án.

---

## BẢN ĐỒ TỔNG QUAN HỆ THỐNG AI

Hệ thống AI của chúng ta gồm 4 trụ cột chính phối hợp nhịp nhàng với nhau:

```
                  ┌───────────────────────────────────────────┐
                  │            Dữ liệu thô (CSV)              │
                  └─────────────────────┬─────────────────────┘
                                        │ (db_seeder.py)
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │           PostgreSQL Nghiệp Vụ            │
                  └──────────────┬─────────────────────┬──────┘
                                 │                     │
       (product-service API)     │                     │ (importer.py)
                                 ▼                     ▼
     ┌─────────────────────────────┐         ┌─────────────────────────────┐
     │    Qdrant (Vector DB)       │         │    Neo4j (Graph DB)         │
     │  - Tìm kiếm theo ngữ nghĩa  │         │  - Mối quan hệ Khách-Hàng   │
     │  - So khớp ý kiến khách hàng│         │  - Hành vi xem, mua, giỏ    │
     └──────────────┬──────────────┘         └──────────────┬──────────────┘
                    │                                       │
                    │               ┌───────────────────────┘
                    ▼               ▼
     ┌─────────────────────────────────────────────────────────────┐
     │                 Recommendation Service                      │
     │     - Nhận diện lịch sử hành vi người dùng                  │
     │     - Rút trích các sản phẩm liên quan từ Neo4j             │
     │     - Lấy ngữ cảnh tương đồng từ Qdrant                     │
     │     - Chấm điểm & xếp hạng bằng mô hình GRU (Deep Learning) │
     └──────────────────────────────┬──────────────────────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │    Giao diện Người dùng     │
                     │  - Đề xuất sản phẩm trang chủ│
                     │  - Tư vấn qua Chatbot (RAG) │
                     └─────────────────────────────┘
```

---

## 1. DỮ LIỆU ĐI TỪ ĐÂU VÀO ĐÂU? (DATA INGESTION FLOW)

Hãy đi từ điểm xuất phát của toàn bộ dữ liệu: các file CSV chứa thông tin ban đầu.

### Bước 1: Từ File CSV vào các Database PostgreSQL nghiệp vụ
*   **Dữ liệu gốc ở đâu?** Nằm trong thư mục [AI/data](file:///home/truong/CodeProject/SAD/AI-Ecom/AI/data) gồm các file như `customer.csv`, `products.csv`, `product_views.csv`, `cart_actions.csv`, `purchase_actions.csv`...
*   **Ai là người đưa dữ liệu đi?** Script [db_seeder.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/db_seeder.py) của service `knowledge_service`.
*   **Tại sao không đẩy thẳng vào Neo4j/Qdrant?** 
    PostgreSQL đóng vai trò là **Source of Truth** (Nguồn sự thật gốc). Tại đây, dữ liệu được làm sạch, chuẩn hóa và khử trùng lặp (ví dụ: gộp các sản phẩm trùng tên, chuẩn hóa danh mục thông qua bản đồ ánh xạ `product_map` và `variant_map`). Sau khi được xử lý tại PostgreSQL, dữ liệu mới sẵn sàng để phân phối đi các cơ sở dữ liệu AI chuyên dụng.
*   **Kết quả:** Dữ liệu được phân bổ vào các DB:
    *   `auth_db`: Chứa tài khoản người dùng và địa chỉ.
    *   `product_db`: Chứa danh mục, sản phẩm, thuộc tính và biến thể sản phẩm.
    *   `tracking_db`: Chứa lịch sử xem sản phẩm, hành động giỏ hàng và lịch sử mua sắm.

### Bước 2: Giả lập Giỏ hàng & Đơn hàng nghiệp vụ
*   Sau khi seed dữ liệu tracking thô, script [sync_operational_db.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/sync_operational_db.py) sẽ đọc lịch sử hành vi mua sắm/thêm giỏ hàng từ `tracking_db` để tái tạo lại trạng thái giỏ hàng thực tế trong `cart_db` và các đơn hàng đã giao trong `order_db`. Điều này giúp hệ thống gợi ý lúc runtime có thể hỏi trực tiếp các API nghiệp vụ để lấy giỏ hàng hiện tại của bạn.

---

## 2. NEO4J (GRAPH DATABASE): TRÁI TIM KẾT NỐI HÀNH VI

Neo4j được sử dụng để xây dựng một bản đồ mạng lưới (Knowledge & Behavior Graph) kết nối giữa Người dùng, Sản phẩm, Danh mục, Lượt tìm kiếm và Voucher khuyến mãi.

### Cách đưa dữ liệu vào Neo4j:
*   **File thực hiện:** [importer.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/importer.py) trong service `knowledge_service`.
*   **Cơ chế hoạt động:**
    1.  **Làm sạch:** Chạy lệnh `MATCH (n) DETACH DELETE n` để xóa sạch toàn bộ đồ thị cũ, đảm bảo không có dữ liệu rác.
    2.  **Tạo ràng buộc:** Tạo các Unique Constraints trên các trường ID để việc tìm kiếm nhanh hơn và tránh trùng lặp node.
    3.  **Import thực tế:** Query dữ liệu trực tiếp từ các PostgreSQL nghiệp vụ (chứ không đọc file CSV) và đẩy vào Neo4j để dựng các Node và Relationship (Mối quan hệ):

| Node (Đối tượng) | Thuộc tính chính |
| :--- | :--- |
| **`User`** | `id`, `email`, `full_name` |
| **`Product`** | `id`, `name`, `price`, `description`, `image_url`, `product_type`, `attributes` |
| **`Category`** | `id`, `name`, `description` |
| **`Voucher`** | `id`, `code`, `discount_type`, `discount_value`, `min_order_value`, `is_active` |
| **`Search`** | `query` (Từ khóa người dùng đã gõ) |

| Relationship (Mối quan hệ) | Ý nghĩa |
| :--- | :--- |
| **`(:Product)-[:BELONGS_TO]->(:Category)`** | Sản phẩm thuộc về danh mục nào |
| **`(:User)-[:VIEWED {timestamp}]->(:Product)`** | Người dùng đã xem sản phẩm này |
| **`(:User)-[:ADDED_TO_CART {timestamp}]->(:Product)`** | Người dùng đã thêm sản phẩm này vào giỏ hàng |
| **`(:User)-[:BOUGHT {timestamp}]->(:Product)`** | Người dùng đã mua sản phẩm này |
| **`(:User)-[:SEARCHED {timestamp}]->(:Search)`** | Người dùng đã tìm kiếm từ khóa này |

---

## 3. QDRANT (VECTOR DATABASE): CƠ SỞ DỮ LIỆU NGỮ NGHĨA

Qdrant dùng để lưu trữ các **Vector Embedding** của sản phẩm phục vụ cho việc tìm kiếm bằng ý nghĩa (Semantic Search) thay vì chỉ so khớp từ khóa thô cứng.

### Cách đưa dữ liệu vào Qdrant:
*   **File thực hiện:** [main.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/vector_service/main.py) trong service `vector_service`.
*   **Cơ chế hoạt động:**
    1.  **Lấy dữ liệu:** Gọi API HTTP GET tới `product-service` để lấy danh sách sản phẩm hiện tại dưới dạng JSON.
    2.  **Tạo văn bản mô tả (Textification):** Hàm `format_product_text(p)` ghép nối tất cả thông tin quan trọng của sản phẩm thành một chuỗi văn bản dài. 
        *   *Ví dụ:* `"Product Name: iPhone 15. Category: Điện thoại. Type: Điện tử. Description: Điện thoại Apple thế hệ mới. Attributes: dung lượng: 128GB, màu sắc: Đen. Options: Đen 128GB, Titan 256GB."`
    3.  **Nhúng Vector (Embedding):** Dùng mô hình Deep Learning cục bộ **`all-MiniLM-L6-v2`** (từ thư viện `sentence_transformers`) để mã hóa đoạn văn bản trên thành một danh sách số thực gồm **384 chiều**. Vector này đại diện cho "vị trí ngữ nghĩa" của sản phẩm trong không gian tri thức.
    4.  **Upsert vào Qdrant:** Tạo Collection tên `products` sử dụng khoảng cách Cosine (`Distance.COSINE`) và đẩy vector kèm payload (ID, tên, giá, ảnh...) vào Qdrant. ID của point trong Qdrant chính là ID sản phẩm trong PostgreSQL.

---

## 4. RUNTIME: AI CHẠY NHƯ THẾ NÀO KHI CÓ REQUEST?

Khi hệ thống đang hoạt động và người dùng thực hiện các hành động trên website, các luồng AI sẽ chạy như sau:

### Luồng 1: Tìm kiếm sản phẩm bằng ngữ nghĩa (Semantic Search)
Khi khách hàng nhập từ khóa tìm kiếm (Ví dụ: *"thiết bị nghe nhạc nhỏ gọn"*):

```
[Người dùng nhập từ khóa] ──> [API Gateway] ──> [recommendation-search-service]
                                                           │
                                                           ▼ (all-MiniLM-L6-v2)
                                                 [Mã hóa từ khóa thành Vector]
                                                           │
                                                           ▼ (So sánh Cosine)
                                                 [Query Qdrant lấy Top sản phẩm]
                                                           │
                                                           ▼
                                                 [Lấy chi tiết từ product-service]
                                                           │
                                                           ▼
                                                 [Hiển thị kết quả tìm kiếm]
```
*   **File xử lý chính:** [search_server.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/vector_service/search_server.py).
*   **Đặc điểm:** Dù sản phẩm không chứa từ khóa *"thiết bị nghe nhạc"*, Qdrant vẫn có thể trả về các sản phẩm như *"iPod"* hoặc *"Tai nghe bluetooth"* vì chúng có sự tương đồng cao về mặt ngữ nghĩa (semantic similarity).

---

### Luồng 2: Gợi ý sản phẩm cá nhân hóa (Personalized Recommendations)
Khi khách hàng truy cập Trang chủ hoặc Giỏ hàng, hệ thống cần hiển thị danh sách *"Có thể bạn cũng thích"*:

*   **File xử lý chính:** [main.py (recommendation_service)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/recommendation_service/main.py) tại endpoint `/api/recommendations/{user_id}`.

#### Quá trình 5 bước để tạo ra gợi ý cá nhân hóa:

#### **Bước 1: Xây dựng lịch sử hành vi (User Profile)**
Hệ thống gọi đồng thời 3 API: `cart-service` (lấy giỏ hàng hiện tại), `order-service` (lấy đơn hàng đã mua) và `tracking-service` (lấy lịch sử xem sản phẩm). Sau đó lọc trùng và xếp theo thứ tự thời gian để lấy ra **20 hành vi gần nhất** của người dùng.

#### **Bước 2: Tìm sản phẩm ứng viên từ Neo4j (Graph Collaborative Filtering)**
Gửi danh sách các sản phẩm trong lịch sử của người dùng (`seed_ids`) vào Neo4j để chạy câu lệnh Cypher tìm các sản phẩm ứng viên:
*   *Ý tưởng thuật toán:* Tìm những người dùng khác cũng từng thêm các `seed_ids` này vào giỏ hàng (`ADDED_TO_CART`). Sau đó xem họ đã xem (`VIEWED`), thêm giỏ (`ADDED_TO_CART`) hay mua (`BOUGHT`) những sản phẩm nào khác.
*   Chấm điểm sơ bộ các sản phẩm này dựa trên trọng số tương tác (`buys * 3.0 + carts * 2.0 + views * 1.0`).

#### **Bước 3: Tìm sản phẩm ứng viên từ Qdrant (Semantic Context)**
Hệ thống ghép lịch sử 20 hành vi của người dùng thành một đoạn văn bản (hành vi mua lặp lại 3 lần, giỏ hàng lặp lại 2 lần để nhấn mạnh mức độ ưu tiên). Sau đó nhúng đoạn văn bản này thành vector và query Qdrant để lấy các sản phẩm tương tự về mặt ngữ nghĩa với xu hướng mua sắm gần đây của user. Những sản phẩm này được gắn nhãn `qdrant_context` (Badge **Semantic** trên giao diện).

#### **Bước 4: Chấm điểm bằng mô hình học máy GRU (Deep Learning)**
Mô hình GRU (`GRU_best_model.h5` kết hợp với `encoders.pkl` để mã hóa hành vi, sản phẩm, danh mục thành số nguyên) sẽ nhận đầu vào là chuỗi 20 hành động gần nhất của user để dự đoán xác suất (probability từ `0.0` đến `1.0`) người dùng sẽ bấm mua từng sản phẩm ứng viên lấy ra từ Neo4j ở Bước 2.

#### **Bước 5: Trộn kết quả & Trả về**
Hệ thống sẽ xếp các sản phẩm có độ tương đồng ngữ nghĩa từ Qdrant (`qdrant_context`) lên đầu tiên để đảm bảo tính thời sự và bám sát ý định tức thời của người dùng. Tiếp theo là các sản phẩm được đề xuất từ Graph Database đã được mô hình GRU chấm điểm và sắp xếp theo thứ tự điểm số từ cao xuống thấp.

---

### Luồng 3: Chatbot tư vấn thông minh (RAG Chatbot)
Khi khách hàng gửi tin nhắn trò chuyện với Chatbot tư vấn:

*   **File xử lý chính:** [main.py (chatbot_service)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/main.py) tại endpoint `/api/chatbot/ask`.

#### Cách thức hoạt động:
1.  **Ghi nhận hành vi thời gian thực:** Nếu tin nhắn của user liên kết với một sản phẩm cụ thể, chatbot sẽ ghi nhận trực tiếp mối quan hệ (`VIEWED`, `ADDED_TO_CART`, `SEARCHED`) vào Neo4j ngay lập tức thông qua [kb_client.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/kb_client.py).
2.  **Truy xuất thông tin sản phẩm (Qdrant):** Gửi tin nhắn của người dùng tới `recommendation-search-service` để tìm kiếm các sản phẩm tương đồng nhất bằng Qdrant.
3.  **Truy xuất chính sách/FAQ (PostgreSQL):** Tìm kiếm các bài viết hướng dẫn đổi trả, giao hàng, bảo hành trong database `chatbot_db` (bảng `knowledge_bases`) bằng phương pháp so khớp từ khóa thô (Keyword Search).
4.  **Truy xuất thông tin đồ thị (Neo4j):** Query Neo4j lấy lịch sử tương tác gần nhất của user, danh sách các Voucher đang hoạt động (`get_active_vouchers`) và các sản phẩm bán chạy.
5.  **Dự đoán xác suất mua (GRU):** Chạy mô hình GRU để xếp hạng các sản phẩm ứng viên tìm được, chọn ra top 3 sản phẩm phù hợp nhất với sở thích của người dùng để chatbot gợi ý.
6.  **Tạo Prompt & Gọi LLM (Gemini):**
    Hợp nhất toàn bộ dữ liệu trên (Lịch sử user + Sản phẩm gợi ý + Chính sách FAQ tìm thấy + Voucher đang có) vào một Prompt ngữ cảnh lớn. Gửi Prompt này đến mô hình ngôn ngữ lớn **Gemini** (thông qua [freellm_client.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/freellm_client.py)).
7.  **Trả phản hồi:** Trả về câu trả lời tự nhiên của Gemini kèm theo danh sách sản phẩm gợi ý hiển thị trực tiếp trên khung chat. Nếu không có cấu hình Gemini API Key, hệ thống sẽ sử dụng bộ sinh câu trả lời mẫu cục bộ (Local Brain).

---

## 5. BẢN CHỈ DẪN FILE CỐT LÕI (AI FILE INDEX)

Khi cần đọc hoặc chỉnh sửa code liên quan đến AI, đây là các file bạn cần tìm:

### 🛠️ Thiết lập & Nạp dữ liệu
*   [db_seeder.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/db_seeder.py): Đọc dữ liệu từ file CSV thô để nạp vào các PostgreSQL nghiệp vụ.
*   [sync_operational_db.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/sync_operational_db.py): Giả lập dữ liệu giỏ hàng/đơn hàng từ tracking.
*   [importer.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/knowledge_service/importer.py): Lấy dữ liệu từ PostgreSQL đồng bộ sang Graph Database Neo4j.
*   [main.py (vector_service)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/vector_service/main.py): Đọc sản phẩm qua API, nhúng vector và đẩy vào Qdrant.

### 🏃 Runtime Services (Xử lý khi hệ thống chạy)
*   [search_server.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/vector_service/search_server.py): Server tiếp nhận request tìm kiếm ngữ nghĩa, nhúng từ khóa tìm kiếm và query Qdrant.
*   [main.py (recommendation_service)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/recommendation_service/main.py): Pipeline gợi ý cá nhân hóa (Xây dựng lịch sử user -> Neo4j candidates -> Qdrant context -> GRU score).
*   [main.py (chatbot_service)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/main.py): Tiếp nhận tin nhắn chat, điều phối luồng lấy sản phẩm (Qdrant), chính sách (Postgres), lịch sử & voucher (Neo4j) để đưa vào Prompt gửi cho LLM.
*   [kb_client.py (chatbot)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/kb_client.py): Các hàm query Cypher tới Neo4j dành riêng cho Chatbot (lấy lịch sử user, lấy voucher, lấy chi tiết sản phẩm).
*   [ai_engine.py (chatbot)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/ai_engine.py): Cài đặt việc load mô hình GRU và dự đoán xác suất mua hàng dành cho Chatbot.
*   [freellm_client.py (chatbot)](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/freellm_client.py): Client đóng gói thông tin ngữ cảnh và giao tiếp với Gemini API.

### 🖥️ Giao diện hiển thị (Templates)
*   [homepage.html](file:///home/truong/CodeProject/SAD/AI-Ecom/services/api_gateway/templates/homepage.html): Gọi API gợi ý và hiển thị danh sách sản phẩm đề xuất kèm theo nhãn `Semantic` hoặc tỷ lệ phần trăm mua (`% Buy`).
*   [cart.html](file:///home/truong/CodeProject/SAD/AI-Ecom/services/api_gateway/templates/cart.html): Hiển thị danh sách sản phẩm khuyên dùng khi khách hàng xem giỏ hàng.
*   [search.html](file:///home/truong/CodeProject/SAD/AI-Ecom/services/api_gateway/templates/search.html): Giao diện tìm kiếm ngữ nghĩa.

---

Hy vọng tài liệu này giúp bạn nắm bắt toàn bộ bức tranh kiến trúc AI của hệ thống một cách nhanh chóng và rõ ràng nhất! Nếu có phần nào bạn muốn đi sâu hơn vào chi tiết dòng code cụ thể, cứ cho mình biết nhé.
