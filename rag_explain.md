# Tài Liệu Giải Thích Chi Tiết Hệ Thống RAG Chatbot (TruongShop)

Tài liệu này phân tích chi tiết cơ chế hoạt động của **RAG Chatbot (Retrieval-Augmented Generation)** tại Dịch vụ Chatbot của hệ thống TruongShop. RAG giúp LLM (Gemini) trả lời chính xác theo chính sách của shop và cá nhân hóa đề xuất sản phẩm dựa trên hành vi thời gian thực của khách hàng.

---

## 1. RAG LÀ GÌ VÀ VAI TRÒ TRONG TRUONGSHOP?

Trong các chatbot thông thường, mô hình ngôn ngữ lớn (LLM) trả lời dựa trên dữ liệu huấn luyện có sẵn. Điều này dẫn đến hai điểm yếu lớn:
1.  **Ảo tưởng (Hallucination):** LLM tự bịa ra thông tin nếu không có sẵn câu trả lời.
2.  **Thiếu tính thời sự:** LLM không biết được giỏ hàng hiện tại, lịch sử xem hàng, các voucher đang hoạt động, hay chính sách nội bộ của cửa hàng.

**Giải pháp RAG (Retrieval-Augmented Generation)** giải quyết vấn đề này qua 3 pha cốt lõi:
1.  **Retrieval (Truy xuất):** Khi user nhắn tin, hệ thống tự động lục tìm dữ liệu thực tế từ **PostgreSQL**, **Neo4j** và **Qdrant**.
2.  **Augmentation (Bổ sung ngữ cảnh):** Nhồi các dữ liệu thực tế tìm được vào một **Prompt** (lời nhắc) gửi cho LLM.
3.  **Generation (Sinh câu trả lời):** LLM đọc hiểu ngữ cảnh đã cung cấp và trả lời khách hàng một cách chính xác nhất.

---

## 2. SƠ ĐỒ LUỒNG RAG CHATBOT TOÀN DIỆN

Dưới đây là sơ đồ chi tiết tiến trình đi của một request từ lúc người dùng nhắn tin cho đến khi nhận được câu trả lời:

```text
                             [Khách hàng nhắn tin]
                                      │
                                      ▼
                                 API Gateway
                             (/api/chatbot/ask)
                                      │
                                      ▼
                         [Chatbot Service: main.py]
                       /              │             \
                      /               │              \
              (Truy xuất)         (Truy xuất)        (Ghi nhận action)
                 /                    │                    \
                ▼                     ▼                     ▼
         ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
         │  Qdrant DB   │      │ PostgreSQL   │      │   Neo4j DB   │
         │(Tìm SP tương │      │(Tìm FAQ/Quy  │      │(Lịch sử user,│
         │  đồng ngữ    │      │    chế)      │      │ Voucher,     │
         │   nghĩa)     │      └──────┬───────┘      │ Ghi action)  │
         └──────┬───────┘             │              └──────┬───────┘
                │                     │             /       │
                │                     │            /        │
                │                     │      (Lịch sử)  (Voucher)
           (Top 5 SP)                 │          /          │
                │                     │         /           │
                ▼                     ▼        ▼            ▼
         ┌──────────────┐             │   ┌────────┐   ┌────────┐
         │ Danh sách    │             │   │ Lịch sử│   │ Voucher│
         │ Ứng viên SP  │             │   │  User  │   │ Active │
         └──────┬───────┘             │   └───┬────┘   └───┬────┘
                │                     │       │            │
           (Lọc bỏ SP đã mua/giỏ)     │       │            │
                │                     │       │            │
                ▼                     │       ▼            │
         ┌──────────────┐             │   ┌────────┐       │
         │  Mô hình     │◄────────────┼───┤  GRU   │       │
         │  Deep GRU    │ (Lịch sử)   │   └────────┘       │
         └──────┬───────┘             │                    │
                │                     │                    │
          (Top 3 SP đề xuất)          │                    │
                │                     │                    │
                ▼                     ▼                    ▼
         ┌──────────────────────────────────────────────────┐
         │             Lắp Ghép Prompt Ngữ Cảnh             │
         │   (Gồm: 3 SP + Lịch sử + FAQ + Voucher Active)   │
         └────────────────────────┬─────────────────────────┘
                                  │
                                  ▼
                      [Gemini API] / [LocalBrain]
                                  │
                                  ▼
                      (Trả về Reply + 3 Card SP)
                                  │
                                  ▼
                          [Khách hàng nhận]
```

---

## 3. BA NGUỒN TRUY XUẤT TRI THỨC (RETRIEVAL PHASE)

Khi nhận câu hỏi của người dùng, chatbot song song truy cập 3 hệ thống cơ sở dữ liệu khác nhau để lấy thông tin:

### A. Tri thức Cứng (PostgreSQL - `chatbot_db`)
*   **Dữ liệu lưu trữ:** Các quy chế, chính sách đổi trả, giao nhận, FAQ do nhân viên cập nhật ở trang quản trị.
*   **Cách truy xuất:** Hàm `search_custom_kb()` thực hiện tách từ khóa của người dùng và so khớp tần suất xuất hiện (Keyword Match) trong tiêu đề và nội dung của bảng `knowledge_bases`. Kết quả trả về là **tối đa 3 quy chế liên quan nhất**.

### B. Tri thức Ngữ nghĩa (Qdrant Vector DB)
*   **Dữ liệu lưu trữ:** Các vector embedding 384 chiều của danh mục sản phẩm.
*   **Cách truy xuất:** Gửi tin nhắn của người dùng tới `recommendation-search-service` để thực hiện tìm kiếm tương đồng vector. Kết quả trả về là **tối đa 5 sản phẩm** sát sườn nhất với mong muốn tìm kiếm (Ví dụ: khách nhắn *"tôi muốn mua áo ấm mùa đông"*, Qdrant sẽ quét ra *"Áo nỉ Hoodie"*).

### C. Tri thức Mạng lưới Hành vi (Neo4j Graph DB)
*   **Dữ liệu lưu trữ:** Biểu đồ mạng lưới kết nối giữa người dùng, sản phẩm, hành vi tương tác và voucher.
*   **Cách truy xuất:**
    1.  Lấy tối đa **10 hành động gần nhất** của user liên quan tới sản phẩm (`get_user_history`) để hiểu sở thích gần đây của họ.
    2.  Lấy tối đa **5 mã voucher** đang kích hoạt để chatbot lồng ghép khuyến mãi vào câu tư vấn.

---

## 4. CHẤM ĐIỂM & TÁI XẾP HẠNG BẰNG AI (RE-RANKING PHASE)

Hệ thống không gửi trực tiếp toàn bộ sản phẩm tìm được cho LLM vì sẽ làm loãng prompt. Thay vào đó, một mô hình AI cục bộ sẽ chấm điểm chọn lọc:
*   **Mô hình sử dụng:** Mạng nơ-ron hồi quy **GRU** được tối ưu hóa cho bài toán gợi ý chuỗi hành vi thời gian thực.
*   **Hoạt động:**
    1.  Gom toàn bộ các sản phẩm ứng viên (Qdrant + Neo4j).
    2.  Lọc bỏ sản phẩm khách hàng đã mua hoặc đã cho vào giỏ hàng gần đây để tránh đề xuất thừa.
    3.  Chạy qua mô hình GRU để dự đoán sản phẩm nào khách hàng có khả năng tương tác tiếp theo cao nhất dựa trên lịch sử hành vi của họ.
    4.  Lọc lấy **3 sản phẩm có điểm dự đoán cao nhất** để hiển thị dạng thẻ card mua hàng.

---

## 5. SINH CÂU TRẢ LỜI CÁ NHÂN HÓA (GENERATION PHASE)

### Cách thức lắp ghép Prompt (Prompt Assembly)
Tất cả tri thức đã truy xuất và chấm điểm ở trên được gộp thành một biến `context_data` và nhồi vào Prompt hệ thống gửi cho Gemini:

```text
Bạn là một trợ lý bán hàng AI thân thiện và chuyên nghiệp của TruongShop.
Sử dụng các thông tin ngữ cảnh dưới đây để trả lời khách hàng bằng tiếng Việt một cách lịch sự, tự nhiên và thuyết phục. 

Ngữ cảnh cửa hàng:
- Lịch sử tương tác của khách hàng: {history}
- Sản phẩm đề xuất dành riêng cho họ: {ai_suggestions}
- Các mã voucher khuyến mãi đang áp dụng: {vouchers}
- Tài liệu quy chế/chính sách liên quan của cửa hàng: {kb_context}

Câu hỏi của khách hàng: "{tin_nhắn_của_user}"
Hãy đưa ra câu trả lời thuyết phục, khéo léo lồng ghép đề xuất sản phẩm và mã voucher để khuyến khích mua hàng.
```

### Gọi LLM & Cơ chế dự phòng (Fallback)
*   **Luồng chính:** Gọi API **Gemini 2.5 Flash** (thông qua [freellm_client.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/freellm_client.py)) gửi kèm Prompt ngữ cảnh trên.
*   **Cơ chế dự phòng:** Nếu Gemini API gặp lỗi hoặc không cấu hình API Key, hệ thống tự động chuyển sang mô hình **Local Brain** (`local_brain.py`). Local Brain sẽ sử dụng các câu trả lời tiếng Việt được định nghĩa sẵn theo dạng template thông minh kết hợp với thông tin sản phẩm và voucher để phản hồi cho khách hàng, đảm bảo chatbot không bao giờ bị sập.

---

## 6. VỊ TRÍ CÁC FILE CODE CHÍNH CỦA RAG CHATBOT

*   [services/chatbot_service/main.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/main.py): File khởi chạy dịch vụ chatbot, chứa endpoint `/api/chatbot/ask` và luồng RAG tổng quát.
*   [services/chatbot_service/chatbot_app/kb_client.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/kb_client.py): Phụ trách query Cypher tới Neo4j để lấy lịch sử user, voucher và ghi nhận action.
*   [services/chatbot_service/chatbot_app/ai_engine.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/ai_engine.py): Phụ trách load model GRU và chấm điểm dự đoán xác suất mua hàng của các sản phẩm ứng viên.
*   [services/chatbot_service/chatbot_app/freellm_client.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/freellm_client.py): Dựng prompt ngữ cảnh và gửi request lên API Gemini.
*   [services/chatbot_service/chatbot_app/local_brain.py](file:///home/truong/CodeProject/SAD/AI-Ecom/services/chatbot_service/chatbot_app/local_brain.py): Giải thuật sinh câu trả lời dự phòng dựa trên template khi LLM lỗi.
