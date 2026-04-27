# E-COMMERCE MICROSERVICES - AGENT DOCUMENTATION
## PROJECT OVERVIEW
**⚠️ LƯU Ý QUAN TRỌNG**: File này PHẢI được cập nhật sau mỗi lần thêm service, thay đổi architecture, hoặc implement feature mới!

**Last Updated**: 2026-04-05 (Multi-Address + Supplier Service + Staff Management)  
**Status**: 100% COMPLETE - EXTENDED STAFF CAPABILITIES

---

## ARCHITECTURE OVERVIEW
### ✅ Phase 1 - Core Infrastructure
- Backend Framework: Django + DRF
- Database: PostgreSQL (10 databases ring bit)
- Message Broker: RabbitMQ
- API Gateway: Custom Django gateway
- Authentication: JWT tokens
- Patterns: Microservices, Saga Choreography, Outbox Pattern

### ✅ Phase 6 - Product Details & UI Refinement
- **Product Detail Page**: Trang chi tiết sản phẩm (Quantity selection, Options, Supplier info, Ratings, Stock status).
- **Staff Dashboard Upgrade**: Bỏ "View Shop", thay bằng "Manage Products" & "Manage Suppliers" ngay tại trung tâm.
- **Improved UX**: 
  - Nút "Detail" bên cạnh "Add to Cart" tại trang chủ.
  - Tab-aware "Add" buttons trong trang Manage Products.
  - Sửa lỗi không edit được Supplier.
  - Thêm nút Close (X) cho tất cả các Modal (Supplier/Product).

---

## SERVICE MAP
API Gateway (8000)
> Auth Service (8001)        [auth_db:5432]    
> Customer Service (8002)    [customer_db:5433]    
> Staff Service (8003)       [staff_db:5434]    
> Book Service (8004)        [book_db:5437]    
> Clothes Service (8005)     [clothes_db:5435]   
> Cart Service (8006)        [cart_db:5436]    
> Order Service (8007)       [order_db:5438]    
> Payment Service (8008)     [payment_db:5439]    
> Voucher Service (8009)     [voucher_db:5440]    
> Rating Service (8010)      [rating_db:5441]    
> Supplier Service (8011)    [supplier_db:5442]

Background Workers:
> auth-publisher              [Auth -> RabbitMQ]
> customer-consumer           [RabbitMQ -> Customer DB]

---

## DATABASE SCHEMAS
### customer_db (Port 5433)
```sql
shipping_addresses (id, customer_id, full_name, phone, address_line, is_default, created_at)
```

### supplier_db (Port 5442)
```sql
suppliers (id, name, contact_name, email, phone, address, is_active, created_at, updated_at)
```

### book_db / clothes_db
```sql
books (..., supplier_id)
clothes (..., supplier_id)
```

---

## API ENDPOINTS
### Added/Updated Endpoints (v3)

**Product Details:**
- GET `/product/detail/<type>/<id>/` - Frontend Route for product detail page.

**Customer Addresses:**
- POST `/api/customer/address/set-default/<id>` - Đặt địa chỉ làm mặc định
- DELETE `/api/customer/address/delete/<id>` - Xoá địa chỉ

**Suppliers (Staff JWT required):**
- GET `/api/suppliers/` - List all suppliers
- POST `/api/suppliers/create/` - Add new supplier
- PUT `/api/suppliers/update/<id>/` - Edit supplier
- DELETE `/api/suppliers/delete/<id>/` - Deactivate supplier

**Product Management (Staff JWT required):**
- POST `/api/books/add/` - Add new book (author, isbn, category, supplier_id)
- PUT `/api/books/update/<id>/` - Edit book
- DELETE `/api/books/delete/<id>/` - Delete book
- POST `/api/clothes/add/` - Add new clothes (size, color, material, supplier_id)
- PUT `/api/clothes/update/<id>/` - Edit clothes
- DELETE `/api/clothes/delete/<id>/` - Delete clothes

---

## FRONTEND PAGES
### Customer Portal
- ✅ **Profile Page**: Quản lý nhiều địa chỉ, hỗ trợ Star (set default), Delete và Add new.
- ✅ **Checkout Page**: Cho phép chọn địa chỉ từ danh sách có sẵn hoặc thêm nhanh địa chỉ mới. Tự động lấy địa chỉ mặc định khi load.
- ✅ **Product Detail**: Xem chi tiết sản phẩm, chọn số lượng, xem thông tin nhà cung cấp và rating.

### Staff Portal
- ✅ **Dashboard**: Trung tâm điều khiển với 3 cột (Orders, Products, Suppliers).
- ✅ **Manage Products**: Trang quản lý kho hàng. Chia Tab Books/Clothes. Nút "Add" tự động cập nhật theo Tab.
- ✅ **Manage Suppliers**: CRUD danh sách nhà cung cấp hàng hoá. Đã sửa lỗi edit.

---

## CHANGELOG
**2026-04-05 - Staff Management & Supplier System:**
- ✅ Created **Supplier Service** for inventory source tracking.
- ✅ Implemented **Multi-Address UX**: Users can manage multiple shipping profiles.
- ✅ Added **Address Synchronization**: Select/Add addresses directly at Checkout or in Profile.
- ✅ Developed **Product Management Console** for Staff: Full CRUD for Books & Clothes.
- ✅ Integrated **Supplier selection** into product creation flow.
- ✅ Added **Staff/Products** and **Staff/Suppliers** navigation links.
- ✅ Updated `quick_start.sh` and `quick_update.sh` to support the expanded cluster.
- ✅ Documented new architecture in `agent.md`.

**2026-04-05 - Product Detail & Staff Dashboard Refinement:**
- ✅ Developed **Product Detail Page** for customers with quantity selector and supplier info.
- ✅ Added "Detail" button to product cards in the homepage.
- ✅ Refined **Staff Dashboard** to focus on management (Orders, Products, Suppliers).
- ✅ Enhanced **Product Management UX** with tab-specific Add buttons.
- ✅ Fixed **Supplier Edit** functionality in the staff portal.
- ✅ Standardized **Modals** with Close (X) buttons for better navigation.
- ✅ Updated `agent.md` to Phase 6.

**2026-04-05 - Unified Combo Management:**
- ✅ Fixed **403 Forbidden** for Suppliers by making the list view public (accessible to guests/customers).
- ✅ Enhanced **Staff Product Edit**: Clicking "Edit" now finds all variations (Sizes/Colors) with the same title and category and loads them into a single management view.
- ✅ Implemented **Dynamic Mass Save/Delete**: Staff can add new variation rows or delete existing ones directly within the Edit modal, with changes reflected in the database on save.
- ✅ Synchronized **Publisher/Supplier Info** across guest and staff views.

**2026-04-05 - AI Chatbot Preparation (Seed Data):**
- ✅ Expanded **Seed Data**: Added 10+ new products (Books & Clothes) to `seed_data.sql` and `quick_start.sh`.
- ✅ Implemented **Rating Dataset**: Generated 50 realistic ratings with **80% English distribution** (40 English, 10 Vietnamese) for cross-lingual AI training.
- ✅ Synchronized **SQL & Python Seeds**: Ensured both `seed_data.sql` and the automated `quick_start.sh` include the rich dataset.

**2026-04-05 - AI Chatbot Service & Infrastructure:**
- ✅ Developed **Chatbot Service**: Microservice structure and database schema ready.
- ⏳ **Knowledge Base (KB)**: Waiting for user to perform fresh model training on production data. All previous mock data and generated artifacts have been removed.
- ✅ Updated **Infrastructure**: `chatbot-service` and `chatbot_db` added to `docker-compose.yml`.
- ✅ Exposed **Gateway Entry**: Added `/api/chatbot/` routing in the API Gateway.

**2026-04-06 - AI Model Integration & Knowledge Base Generation:**
- ✅ **AI Model Trained**: User trained BERT multilingual model on Amazon reviews (100k samples, 2 epochs).
- ✅ **Knowledge Base Generated**: Created `generate_knowledge_base_from_model.ipynb` notebook to:
  - Load trained model from `AI/model/amazon_sentiment_final/`
  - Parse 50 ratings from `seed_data.sql`
  - Use AI model to predict sentiment (1-5 stars) for each comment
  - Generate knowledge base entries with sentiment analysis
  - Export SQL INSERT statements
- ✅ **Model Accuracy**: Achieved good accuracy on seed data with confidence scoring.
- ✅ **Chatbot Service Updated**:
  - Updated `KnowledgeBase` model to match generated SQL structure
  - Enhanced chatbot logic with similarity matching algorithm
  - Added `/api/chatbot/stats/` endpoint for KB statistics
  - Improved query matching with confidence scoring
- ✅ **Import Script**: Created `import_knowledge_base.sh` for easy KB deployment.
- ✅ **Total KB Entries**: 16 product entries (books + clothes) with AI sentiment analysis.

**2026-04-06 - RAG Implementation & Frontend Integration:**
- ✅ **RAG Service Implemented**: 
  - Created `rag_service.py` with sentence transformers for semantic search
  - Supports both transformer-based and fallback encoding
  - Cosine similarity matching with keyword boosting
  - Embeddings caching for performance
- ✅ **Dependencies Added**: `sentence-transformers`, `numpy` to requirements.txt
- ✅ **Enhanced Chatbot Views**: 
  - Integrated RAG service into chatbot_ask endpoint
  - Returns top-3 matches with confidence scores
  - Method tracking (rag_semantic_search, rag_low_confidence, etc.)
- ✅ **Frontend Chat Widget**:
  - Beautiful floating chat button on homepage
  - Real-time messaging interface with typing indicators
  - Quick question buttons for common queries
  - Confidence score display
  - Responsive design for mobile/desktop
- ✅ **Quick Start Integration**: 
  - Updated `quick_start.sh` to auto-import knowledge base
  - Added chatbot status to startup sequence
  - Automatic verification of KB entries

---

**Status**: 🤖✨ AI CHATBOT WITH RAG - FULLY DEPLOYED!  
**Total Implementation**: **100% (Phase 8 Complete - RAG + Frontend)**  
**Features**:
  - ✅ RAG-powered semantic search
  - ✅ BERT multilingual sentiment model
  - ✅ 16 AI-generated knowledge base entries
  - ✅ Interactive chat widget on homepage
  - ✅ Real-time responses with confidence scoring
  - ✅ One-command deployment (`./quick_start.sh`)

**Usage**: 
1. Run: `./quick_start.sh`
2. Visit: http://localhost:8000
3. Click 💬 chat bubble to start chatting!

---

---

🎉 **HỆ THỐNG TRUONGSHOP ĐÃ ĐƯỢC NÂNG CẤP TOÀN DIỆN!** 🚀
