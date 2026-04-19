# 🏗️ TRUONGSHOP MICROSERVICES ARCHITECTURE

```
╔══════════════════════════════════════════════════════════════════════════╗
║                      TRUONGSHOP E-COMMERCE SYSTEM                       ║
║                         MICROSERVICES ARCHITECTURE                      ║
║                              Phase 8 Complete                           ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**System Overview**: E-commerce platform với 11 microservices và message-driven architecture.

**Last Updated**: 2026-04-14  
**Implementation Status**: ✅ 100% Complete

---

## 📐 OVERALL SYSTEM ARCHITECTURE

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[🌐 Web Frontend<br/>Django Templates + JavaScript]
    end
    
    subgraph "API Gateway Layer (Aggregator)"
        GW[🚪 API Gateway :8000<br/>🛡️ Aggregator Pattern<br/>Unified Product Entry]
    end
    
    subgraph "Authentication Layer"
        AUTH[🔐 Auth Service :8001<br/>JWT Token Management]
        AUTHDB[(🗃️ auth_db :5432)]
        AUTHPUB[📤 Auth Publisher]
    end

    subgraph "Distributed Product Network"
        BK[📚 Book Service :8021]
        CL[👕 Clothes Service :8022]
        LP[💻 Laptop Service :8023]
        PH[📱 Phone Service :8024]
        TB[📟 Tablet Service :8025]
        CAM[📷 Camera Service :8026]
        HP[🎧 Headphone Service :8027]
        WT[⌚ Watch Service :8028]
        SH[👟 Shoe Service :8029]
        FN[🛋️ Furniture Service :8030]
        PROD[📦 Product Service :8004]
    end
    
    subgraph "AI & Analytics"
        REC[✨ Recommendation Service :8101]
        VEC[🧪 Vector Sync Tool]
        QDR[💎 Qdrant DB :6333]
        TRACK[📊 Tracking Service :8010]
    end
    
    subgraph "Core Business Services"
        CUST[👥 Customer Service :8002]
        STAFF[👨‍💼 Staff Service :8003]
        SUPP[🏭 Supplier Service :8011]
        CART[🛒 Cart Service :8006]
        ORDER[📦 Order Service :8007]
        PAY[💳 Payment Service :8008]
        VOUCH[🎟️ Voucher Service :8009]
        RATE[⭐ Rating Service :8005]
    end
    
    subgraph "Message Broker Layer"
        MQ[🐰 RabbitMQ :5672]
        CUSTCONS[📥 Customer Consumer]
    end

    %% Connections
    FE --> GW
    FE --> REC
    
    %% Aggregator Logic
    GW -- "Scatter/Gather" --> Distributed Product Network
    
    GW --> AUTH
    GW --> Core Business Services
    GW --> TRACK
    
    %% AI Pipeline
    VEC -- "Embeddings" --> QDR
    REC -- "Search" --> QDR
    TRACK -- "User Profile" --> REC
    
    AUTH --> AUTHDB
    AUTH --> AUTHPUB
    AUTHPUB --> MQ
    MQ --> CUSTCONS
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef gateway fill:#f3e5f5
    classDef product fill:#fff9c4
    classDef ai fill:#fce4ec
    classDef business fill:#e8f5e8
    
    class FE frontend
    class GW gateway
    class BK,CL,LP,PH,TB,CAM,HP,WT,SH,FN,PROD product
    class REC,VEC,QDR,TRACK ai
    class CUST,STAFF,SUPP,CART,ORDER,PAY,VOUCH,RATE business
```

---

## 🔧 SERVICE DETAILS & FUNCTIONS

### 🚪 **API Gateway Service** (:8000)
```
┌─────────────────────────────────────────────────────────────────┐
│  🚪 API GATEWAY - Central Entry Point                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Request routing to appropriate microservices                │
│  • Load balancing across service instances                     │
│  • Authentication middleware                                   │
│  • Response aggregation (Scatter-Gather Pattern)               │
│  • Logic: GET /api/products/ parallel queries 11 services        │
│  • Unified Product Schema for frontend simplicity              │
│  • Static file serving (CSS, JS, images)                     │
│  • Frontend template rendering                               │
│                                                                 │
│  🔗 Routes:                                                     │
│  • /api/auth/* → Auth Service                                 │
│  • /api/customer/* → Customer Service                         │
│  • /api/books/* → Book Service                               │
│  • /api/clothes/* → Clothes Service                          │
│  • /api/cart/* → Cart Service                               │
│  • /api/orders/* → Order Service                            │
│                                                                 │
│  ⚙️ Technology Stack:                                          │
│  • Django 4.2 + Django REST Framework                        │
│  • JWT Authentication                                         │
│  • CORS Headers                                              │
│  • Static Files Management                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🔐 **Authentication Service** (:8001)
```
┌─────────────────────────────────────────────────────────────────┐
│  🔐 AUTH SERVICE - Identity & Access Management                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • User registration & login (Customer + Staff)               │
│  • JWT token generation & validation                          │
│  • Password hashing with PBKDF2                              │
│  • Session management                                         │
│  • User profile CRUD operations                              │
│  • Event publishing for user changes                         │
│                                                                 │
│  🗃️ Database: auth_db (:5432)                                 │
│  Tables:                                                       │
│  • customers (id, email, password_hash, full_name, phone,     │
│              address, is_active, created_at, updated_at)      │
│  • staff (id, email, password_hash, full_name, phone, role,   │
│           is_active, created_at, updated_at)                  │
│  • outbox_events (event publishing)                          │
│                                                                 │
│  📡 Events Published:                                          │
│  • customer_created → Customer Service                       │
│  • customer_updated → Customer Service                       │
│  • staff_created → Staff Service                            │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /register/ - User registration                       │
│  • POST /login/ - User authentication                        │
│  • POST /logout/ - Session termination                       │
│  • GET /profile/ - Get user profile                         │
│  • PUT /profile/ - Update user profile                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 👥 **Customer Service** (:8002)
```
┌─────────────────────────────────────────────────────────────────┐
│  👥 CUSTOMER SERVICE - Customer Data Management                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Customer profile synchronization from Auth Service         │
│  • Multiple shipping address management                       │
│  • Customer preferences & settings                           │
│  • Customer analytics & reporting                            │
│  • Address validation & geocoding                            │
│                                                                 │
│  🗃️ Database: customer_db (:5433)                             │
│  Tables:                                                       │
│  • customers (auth_customer_id, email, full_name, phone,      │
│              address, is_active, created_at, updated_at)      │
│  • shipping_addresses (id, customer_id, full_name, phone,     │
│                       address_line, is_default, created_at)   │
│                                                                 │
│  📥 Events Consumed:                                           │
│  • customer_created (from Auth Service)                      │
│  • customer_updated (from Auth Service)                      │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • GET /profile/ - Get customer profile                      │
│  • PUT /profile/ - Update customer profile                   │
│  • POST /address/add/ - Add shipping address                 │
│  • PUT /address/update/<id>/ - Update address                │
│  • DELETE /address/delete/<id>/ - Delete address             │
│  • POST /address/set-default/<id>/ - Set default address     │
│                                                                 │
│  ⚙️ Event-Driven Architecture:                                │
│  • RabbitMQ consumer for Auth events                         │
│  • Saga pattern for data consistency                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 👨‍💼 **Staff Service** (:8003)
```
┌─────────────────────────────────────────────────────────────────┐
│  👨‍💼 STAFF SERVICE - Admin & Management Portal              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Staff profile management                                   │
│  • Role-based access control (Admin, Manager, Employee)      │
│  • Dashboard analytics & KPIs                                │
│  • Order management & fulfillment                           │
│  • Inventory oversight                                       │
│  • Customer support tools                                   │
│                                                                 │
│  🗃️ Database: staff_db (:5434)                               │
│  Tables:                                                       │
│  • staff (auth_staff_id, email, full_name, phone, role,      │
│           department, is_active, created_at, updated_at)      │
│  • staff_sessions (session tracking)                         │
│                                                                 │
│  🎯 Management Features:                                       │
│  • Product Management (Books + Clothes)                      │
│  • Supplier Management                                       │
│  • Order Processing & Tracking                              │
│  • Customer Service Tools                                   │
│  • Analytics Dashboard                                      │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • GET /dashboard/ - Analytics dashboard                     │
│  • GET /orders/ - Order management                          │
│  • GET /products/ - Product management                      │
│  • GET /suppliers/ - Supplier management                    │
│  • POST /products/add/ - Add new product                    │
│  • PUT /products/update/<id>/ - Update product              │
│                                                                 │
│  🔒 Security:                                                 │
│  • JWT-based authentication                                  │
│  • Role-based authorization                                 │
│  • Admin-only operations                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📦 **Product Service** (:8004)
```
┌─────────────────────────────────────────────────────────────────┐
│  📦 PRODUCT SERVICE - Unified Catalog & Inventory                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Unified catalog for all product types (Books, Clothes, etc.) │
│  • Multi-attribute support via JSON (Author, Material, etc.)    │
│  • Variant/Combo management (Color, Size, Format)               │
│  • Real-time stock tracking per variant combination             │
│  • Cross-category search & advanced filtering                  │
│  • Supplier mapping & inventory health monitoring              │
│                                                                 │
│  🗃️ Database: product_db (:5435)                               │
│  Tables:                                                       │
│  • products (id, name, description, price, product_type,       │
│              category, attributes[JSON], image_url, etc.)      │
│  • product_variants (id, product_id, name, stock, sku,         │
│                      price_override, options[JSON])            │
│                                                                 │
│  🏗️ Flexible Schema:                                            │
│  • Attributes: Stores specialized data based on product_type   │
│  • Variants: Handles combinations (e.g., T-Shirt Red + XL)      │
│  • Combo Pricing: Base price with variant-specific overrides    │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • GET /products/ - List all products (filter by type/cat)      │
│  • GET /products/<id>/ - Get full details with variants        │
│  • POST /products/add/ - Create new product (Staff only)       │
│  • PATCH /products/update/<id>/ - Update product info          │
│  • GET /products/variant/<id>/stock/ - Fetch variant inventory │
│  • POST /products/update-stock/ - Transactional stock changes  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📚 **Book Service** (:8021)
```
┌─────────────────────────────────────────────────────────────────┐
│  📚 BOOK SERVICE - Category Catalog (Books)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Book-only catalog & search                                  │
│  • Category/genre filtering                                    │
│  • Attributes via JSON (author, isbn, publisher, language)     │
│  • Variant handling (format: Hardcover/Paperback)              │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: book_db                                           │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /books/ - List books                                    │
│  • GET /books/<id>/ - Book details                             │
│  • GET /books/categories/ - Categories                         │
│  • POST /books/manage/ - Create/Update (Staff)                 │
│  • DELETE /books/manage/delete/<id>/ - Delete (Staff)          │
│  • POST /books/update-stock/ - Stock update                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 👕 **Clothes Service** (:8022)
```
┌─────────────────────────────────────────────────────────────────┐
│  👕 CLOTHES SERVICE - Category Catalog (Clothes)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Apparel catalog & search                                    │
│  • Category filtering                                          │
│  • Attributes via JSON (size, color, material, brand)          │
│  • Variant handling (size/color combinations)                  │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: clothes_db                                        │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /clothes/ - List clothes                                │
│  • GET /clothes/<id>/ - Clothes details                        │
│  • GET /clothes/categories/ - Categories                       │
│  • POST /clothes/manage/ - Create/Update (Staff)               │
│  • DELETE /clothes/manage/delete/<id>/ - Delete (Staff)        │
│  • POST /clothes/update-stock/ - Stock update                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 💻 **Laptop Service** (:8023)
```
┌─────────────────────────────────────────────────────────────────┐
│  💻 LAPTOP SERVICE - Category Catalog (Laptops)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Laptop catalog & search                                     │
│  • Category filtering                                          │
│  • Attributes via JSON (cpu, ram, storage, gpu)                │
│  • Variant handling (config combinations)                      │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: laptop_db                                         │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /laptops/ - List laptops                                │
│  • GET /laptops/<id>/ - Laptop details                         │
│  • GET /laptops/categories/ - Categories                       │
│  • POST /laptops/manage/ - Create/Update (Staff)               │
│  • DELETE /laptops/manage/delete/<id>/ - Delete (Staff)        │
│  • POST /laptops/update-stock/ - Stock update                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📱 **Phone Service** (:8024)
```
┌─────────────────────────────────────────────────────────────────┐
│  📱 PHONE SERVICE - Category Catalog (Phones)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Phone catalog & search                                      │
│  • Category filtering                                          │
│  • Attributes via JSON (brand, chipset, storage, camera)       │
│  • Variant handling (storage/color combinations)               │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: phone_db                                          │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /phones/ - List phones                                  │
│  • GET /phones/<id>/ - Phone details                           │
│  • GET /phones/categories/ - Categories                        │
│  • POST /phones/manage/ - Create/Update (Staff)                │
│  • DELETE /phones/manage/delete/<id>/ - Delete (Staff)         │
│  • POST /phones/update-stock/ - Stock update                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📟 **Tablet Service** (:8025)
```
┌─────────────────────────────────────────────────────────────────┐
│  📟 TABLET SERVICE - Category Catalog (Tablets)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Tablet catalog & search                                     │
│  • Category filtering                                          │
│  • Attributes via JSON (screen, chipset, storage, battery)     │
│  • Variant handling (storage/color combinations)               │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: tablet_db                                         │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /tablets/ - List tablets                                │
│  • GET /tablets/<id>/ - Tablet details                         │
│  • GET /tablets/categories/ - Categories                       │
│  • POST /tablets/manage/ - Create/Update (Staff)               │
│  • DELETE /tablets/manage/delete/<id>/ - Delete (Staff)        │
│  • POST /tablets/update-stock/ - Stock update                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📷 **Camera Service** (:8026)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 CAMERA SERVICE - Category Catalog (Cameras)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Camera catalog & search                                     │
│  • Category filtering                                          │
│  • Attributes via JSON (sensor, lens, resolution, mount)       │
│  • Variant handling (lens/kit combinations)                    │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: camera_db                                         │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /cameras/ - List cameras                                │
│  • GET /cameras/<id>/ - Camera details                         │
│  • GET /cameras/categories/ - Categories                       │
│  • POST /cameras/manage/ - Create/Update (Staff)               │
│  • DELETE /cameras/manage/delete/<id>/ - Delete (Staff)        │
│  • POST /cameras/update-stock/ - Stock update                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🎧 **Headphone Service** (:8027)
```
┌─────────────────────────────────────────────────────────────────┐
│  🎧 HEADPHONE SERVICE - Category Catalog (Headphones)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Headphone catalog & search                                  │
│  • Category filtering                                          │
│  • Attributes via JSON (driver, type, wireless, mic)           │
│  • Variant handling (color/edition combinations)               │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: headphone_db                                      │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /headphones/ - List headphones                          │
│  • GET /headphones/<id>/ - Headphone details                   │
│  • GET /headphones/categories/ - Categories                    │
│  • POST /headphones/manage/ - Create/Update (Staff)            │
│  • DELETE /headphones/manage/delete/<id>/ - Delete (Staff)     │
│  • POST /headphones/update-stock/ - Stock update               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ⌚ **Watch Service** (:8028)
```
┌─────────────────────────────────────────────────────────────────┐
│  ⌚ WATCH SERVICE - Category Catalog (Watches)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Watch catalog & search                                      │
│  • Category filtering                                          │
│  • Attributes via JSON (movement, material, size, strap)       │
│  • Variant handling (strap/color combinations)                 │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: watch_db                                          │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /watches/ - List watches                                │
│  • GET /watches/<id>/ - Watch details                          │
│  • GET /watches/categories/ - Categories                       │
│  • POST /watches/manage/ - Create/Update (Staff)               │
│  • DELETE /watches/manage/delete/<id>/ - Delete (Staff)        │
│  • POST /watches/update-stock/ - Stock update                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 👟 **Shoe Service** (:8029)
```
┌─────────────────────────────────────────────────────────────────┐
│  👟 SHOE SERVICE - Category Catalog (Shoes)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Shoe catalog & search                                       │
│  • Category filtering                                          │
│  • Attributes via JSON (size, material, gender, brand)         │
│  • Variant handling (size/color combinations)                  │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: shoe_db                                           │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /shoes/ - List shoes                                    │
│  • GET /shoes/<id>/ - Shoe details                             │
│  • GET /shoes/categories/ - Categories                         │
│  • POST /shoes/manage/ - Create/Update (Staff)                 │
│  • DELETE /shoes/manage/delete/<id>/ - Delete (Staff)          │
│  • POST /shoes/update-stock/ - Stock update                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🛋️ **Furniture Service** (:8030)
```
┌─────────────────────────────────────────────────────────────────┐
│  🛋️ FURNITURE SERVICE - Category Catalog (Furniture)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Furniture catalog & search                                  │
│  • Category filtering                                          │
│  • Attributes via JSON (material, dimensions, style, brand)    │
│  • Variant handling (color/size combinations)                  │
│  • Stock tracking per variant                                  │
│                                                                 │
│  🗃️ Database: furniture_db                                      │
│  Tables: products, product_variants, categories                │
│                                                                 │
│  🔗 API Endpoints:                                              │
│  • GET /furniture/ - List furniture                            │
│  • GET /furniture/<id>/ - Furniture details                    │
│  • GET /furniture/categories/ - Categories                     │
│  • POST /furniture/manage/ - Create/Update (Staff)             │
│  • DELETE /furniture/manage/delete/<id>/ - Delete (Staff)      │
│  • POST /furniture/update-stock/ - Stock update                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🚀 **Distributed Product network** (10+ Services)
```
┌─────────────────────────────────────────────────────────────────┐
│  📦 DISTRIBUTED CATALOG - Category Specialized Services         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Services:                                                  │
│  • book-service (:8021)      • furniture-service (:8030)      │
│  • clothes-service (:8022)   • shoe-service (:8029)           │
│  • laptop-service (:8023)    • watch-service (:8028)          │
│  • phone-service (:8024)     • headphone-service (:8027)      │
│  • tablet-service (:8025)    • camera-service (:8026)         │
│                                                                 │
│  📋 Shared Logic (Cloned Template):                             │
│  • Independent database per category (laptop_db, book_db, etc.)│
│  • Specialized attributes per type                             │
│  • Independent scaling & maintenance                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ✨ **AI Recommendation Service** (:8101)
```
┌─────────────────────────────────────────────────────────────────┐
│  ✨ RECOMMENDATION SERVICE - AI Weighted Ranker                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Hybrid recommendation merging view/cart/purchase data       │
│  • Weighted Average Vector calculation (384-dimensional)        │
│  • Vector similarity search via Qdrant                         │
│  • Relevance-based sorting (highest score prioritized)          │
│                                                                 │
│  💎 Vector Storage: Qdrant (:6333)                             │
│  • Collection: "products"                                      │
│  • Metric: Cosine Similarity                                   │
│                                                                 │
│  🧪 Vector Sync Service:                                        │
│  • Mandatory one-time sync tool                                │
│  • Generates embeddings using 'all-MiniLM-L6-v2'               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
```

### 🛒 **Cart Service** (:8006)
```
┌─────────────────────────────────────────────────────────────────┐
│  🛒 CART SERVICE - Shopping Cart Management                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Shopping cart session management                           │
│  • Item addition, removal, quantity updates                   │
│  • Cart persistence across sessions                           │
│  • Price calculation & tax computation                        │
│  • Inventory validation before checkout                       │
│  • Cart abandonment tracking                                  │
│                                                                 │
│  🗃️ Database: cart_db (:5436)                                 │
│  Tables:                                                       │
│  • cart_items (id, customer_id, product_type, product_id,     │
│                name, price, quantity, added_at)               │
│                                                                 │
│  🛍️ Cart Operations:                                          │
│  • Add items from Books or Clothes services                   │
│  • Update quantities with stock validation                    │
│  • Remove individual items or clear cart                      │
│  • Calculate subtotals and totals                             │
│  • Apply vouchers and discounts                               │
│                                                                 │
│  💰 Price Calculation:                                         │
│  • Item price × quantity                                      │
│  • Discount application                                       │
│  • Tax calculation by region                                  │
│  • Shipping cost estimation                                   │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • GET /cart/ - Get cart contents                            │
│  • POST /cart/add/ - Add item to cart                        │
│  • PUT /cart/update/<id>/ - Update item quantity             │
│  • DELETE /cart/remove/<id>/ - Remove item from cart         │
│  • DELETE /cart/clear/ - Clear entire cart                   │
│  • GET /cart/total/ - Get cart total                         │
│                                                                 │
│  🔒 Security Features:                                        │
│  • Customer-specific cart isolation                          │
│  • JWT authentication required                               │
│  • Session timeout handling                                  │
│                                                                 │
│  ⚡ Performance Optimizations:                                │
│  • Redis caching for cart sessions                           │
│  • Optimistic concurrency control                            │
│  • Batch operations for multiple items                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📦 **Order Service** (:8007)
```
┌─────────────────────────────────────────────────────────────────┐
│  📦 ORDER SERVICE - Order Processing & Fulfillment             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Order creation from cart checkout                          │
│  • Order status tracking & updates                           │
│  • Inventory reservation & allocation                         │
│  • Shipping address management                               │
│  • Order history & customer portal                           │
│  • Fulfillment workflow orchestration                        │
│                                                                 │
│  🗃️ Database: order_db (:5438)                                │
│  Tables:                                                       │
│  • orders (id, customer_id, total_amount, status,            │
│            shipping_address, created_at, updated_at)          │
│  • order_items (id, order_id, product_type, product_id,      │
│                 name, price, quantity)                        │
│                                                                 │
│  📋 Order Lifecycle:                                          │
│  1. PENDING - Order created, payment pending                  │
│  2. CONFIRMED - Payment confirmed, inventory reserved         │
│  3. PROCESSING - Items being prepared                         │
│  4. SHIPPED - Order dispatched to customer                    │
│  5. DELIVERED - Order received by customer                    │
│  6. CANCELLED - Order cancelled by customer/system            │
│                                                                 │
│  🚚 Fulfillment Process:                                       │
│  • Inventory check & reservation                              │
│  • Payment verification                                       │
│  • Picking list generation                                    │
│  • Packaging & labeling                                       │
│  • Carrier selection & tracking                               │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /orders/create/ - Create new order                   │
│  • GET /orders/ - List customer orders                       │
│  • GET /orders/<id>/ - Get order details                     │
│  • PUT /orders/<id>/status/ - Update order status (Staff)    │
│  • GET /orders/<id>/tracking/ - Get tracking info            │
│                                                                 │
│  📊 Analytics & Reporting:                                     │
│  • Order volume metrics                                       │
│  • Revenue tracking                                           │
│  • Fulfillment time analysis                                  │
│  • Customer order patterns                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 💳 **Payment Service** (:8008)
```
┌─────────────────────────────────────────────────────────────────┐
│  💳 PAYMENT SERVICE - Payment Processing & Gateway             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Payment method management                                  │
│  • Credit card processing & validation                        │
│  • Payment gateway integration                                │
│  • Transaction history & receipts                             │
│  • Refund & chargeback handling                              │
│  • PCI compliance & security                                 │
│                                                                 │
│  🗃️ Database: payment_db (:5439)                              │
│  Tables:                                                       │
│  • payments (id, order_id, amount, method, status,           │
│              transaction_id, created_at, updated_at)          │
│  • payment_methods (id, customer_id, type, last4,            │
│                     expiry, is_default, created_at)          │
│                                                                 │
│  💰 Payment Methods Supported:                                │
│  • Credit/Debit Cards (Visa, MasterCard, American Express)   │
│  • Digital Wallets (PayPal, Apple Pay, Google Pay)           │
│  • Bank Transfers                                            │
│  • Buy Now, Pay Later (BNPL)                                │
│  • Cryptocurrency (Bitcoin, Ethereum)                        │
│                                                                 │
│  🔒 Security Features:                                        │
│  • PCI DSS compliance                                        │
│  • End-to-end encryption                                     │
│  • Tokenization of sensitive data                            │
│  • Fraud detection & prevention                              │
│  • 3D Secure authentication                                  │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /payments/process/ - Process payment                 │
│  • GET /payments/history/ - Payment history                  │
│  • POST /payments/refund/ - Process refund                   │
│  • GET /payments/<id>/receipt/ - Generate receipt            │
│  • POST /methods/add/ - Add payment method                   │
│                                                                 │
│  🏦 Gateway Integrations:                                      │
│  • Stripe API for card processing                            │
│  • PayPal SDK for wallet payments                            │
│  • Bank APIs for direct transfers                            │
│  • Webhook handling for async notifications                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🎟️ **Voucher Service** (:8009)
```
┌─────────────────────────────────────────────────────────────────┐
│  🎟️ VOUCHER SERVICE - Discount & Promotion Management          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Discount voucher creation & management                     │
│  • Promotional campaign orchestration                         │
│  • Usage tracking & analytics                                │
│  • Code generation & validation                              │
│  • Customer-specific offers                                  │
│  • Seasonal & event-based promotions                         │
│                                                                 │
│  🗃️ Database: voucher_db (:5440)                              │
│  Tables:                                                       │
│  • vouchers (id, code, name, description, discount_type,     │
│              discount_value, min_order_amount, usage_limit,   │
│              used_count, is_active, expires_at, created_at)   │
│  • voucher_usage (id, voucher_id, customer_id, order_id,     │
│                  used_at)                                     │
│                                                                 │
│  🏷️ Voucher Types:                                            │
│  • PERCENTAGE - Percentage discount (e.g., 10% off)          │
│  • FIXED_AMOUNT - Fixed amount discount (e.g., $5 off)       │
│  • FREE_SHIPPING - Free shipping voucher                     │
│  • BUY_ONE_GET_ONE - BOGO promotions                         │
│  • FIRST_TIME_BUYER - New customer discounts                 │
│                                                                 │
│  🎯 Campaign Management:                                       │
│  • Seasonal promotions (Black Friday, Christmas)             │
│  • Customer lifecycle campaigns                              │
│  • Product-specific discounts                                │
│  • Loyalty program rewards                                   │
│  • Referral bonuses                                          │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /vouchers/create/ - Create new voucher (Staff)       │
│  • GET /vouchers/ - List all vouchers                        │
│  • POST /vouchers/validate/ - Validate voucher code          │
│  • POST /vouchers/apply/ - Apply voucher to order            │
│  • GET /vouchers/usage/<code>/ - Get usage statistics        │
│                                                                 │
│  📊 Analytics Features:                                        │
│  • Voucher performance tracking                              │
│  • Conversion rate analysis                                  │
│  • Customer acquisition cost                                 │
│  • ROI calculation per campaign                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ⭐ **Rating Service** (:8010)
```
┌─────────────────────────────────────────────────────────────────┐
│  ⭐ RATING SERVICE - Review & Rating System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Customer review collection & management                    │
│  • Star rating system (1-5 stars)                           │
│  • Review moderation & filtering                             │
│  • Sentiment analysis integration                            │
│  • Review helpfulness voting                                 │
│  • Product recommendation engine                             │
│                                                                 │
│  🗃️ Database: rating_db (:5441)                               │
│  Tables:                                                       │
│  • ratings (id, order_id, customer_id, product_type,         │
│             product_id, product_name, stars, comment,         │
│             created_at)                                       │
│                                                                 │
│  ⭐ Rating Features:                                           │
│  • 5-star rating system                                       │
│  • Written review comments                                    │
│  • Verified purchase validation                               │
│  • Photo/video attachments                                    │
│  • Helpful/unhelpful voting                                   │
│                                                                 │
│  🤖 AI Integration:                                            │
│  • Sentiment analysis on review text                          │
│  • Automated spam detection                                   │
│  • Review quality scoring                                     │
│  • Product recommendation based on reviews                    │
│  • Trend analysis & insights                                  │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /ratings/create/ - Submit new rating                 │
│  • GET /ratings/product/<type>/<id>/ - Get product ratings   │
│  • GET /ratings/customer/ - Get customer's ratings           │
│  • PUT /ratings/update/<id>/ - Update rating                 │
│  • DELETE /ratings/delete/<id>/ - Delete rating              │
│                                                                 │
│  📊 Analytics & Insights:                                      │
│  • Average rating calculations                                │
│  • Rating distribution charts                                 │
│  • Review sentiment trends                                    │
│  • Product performance metrics                                │
│  • Customer satisfaction scores                               │
└─────────────────────────────────────────────────────────────────┘
```

### 🏭 **Supplier Service** (:8011)
```
┌─────────────────────────────────────────────────────────────────┐
│  🏭 SUPPLIER SERVICE - Vendor & Supply Chain Management        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Supplier registration & onboarding                         │
│  • Vendor relationship management (VRM)                       │
│  • Supply chain visibility & tracking                         │
│  • Purchase order management                                  │
│  • Supplier performance monitoring                            │
│  • Contract & compliance management                           │
│                                                                 │
│  🗃️ Database: supplier_db (:5442)                             │
│  Tables:                                                       │
│  • suppliers (id, name, contact_name, email, phone,          │
│               address, is_active, created_at, updated_at)     │
│                                                                 │
│  🏢 Supplier Management:                                       │
│  • Vendor contact information                                 │
│  • Product catalog from suppliers                             │
│  • Pricing & contract terms                                   │
│  • Delivery schedules & lead times                            │
│  • Quality ratings & certifications                           │
│                                                                 │
│  📈 Performance Metrics:                                       │
│  • On-time delivery rates                                     │
│  • Quality scores                                             │
│  • Cost competitiveness                                       │
│  • Customer satisfaction impact                               │
│  • Return/defect rates                                        │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • GET /suppliers/ - List all suppliers                      │
│  • POST /suppliers/create/ - Add new supplier (Staff)        │
│  • PUT /suppliers/update/<id>/ - Update supplier (Staff)     │
│  • DELETE /suppliers/delete/<id>/ - Deactivate supplier      │
│  • GET /suppliers/<id>/performance/ - Performance metrics    │
│                                                                 │
│  📊 Supply Chain Analytics:                                    │
│  • Supplier diversity reporting                               │
│  • Cost analysis & optimization                               │
│  • Risk assessment & mitigation                               │
│  • Sustainability metrics                                     │
│                                                                 │
│  🤝 Integration Points:                                        │
│  • Product Service - Consolidated suppliers                    │
│  • Order Service - Fulfillment coordination                   │
│  • Staff Service - Procurement management                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📊 **Tracking Service** (:8012)
```
┌─────────────────────────────────────────────────────────────────┐
│  📊 TRACKING SERVICE - User Analytics & History                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Tracking user search history and query performance          │
│  • Logging product view events for behavioral analysis         │
│  • Session-based activity monitoring                           │
│  • Data aggregation for personalized recommendations          │
│                                                                 │
│  🗃️ Database: tracking_db (:5443)                              │
│  Tables:                                                       │
│  • search_history (id, customer_id, query, timestamp)          │
│  • product_views (id, customer_id, product_id, type, etc.)     │
│                                                                 │
│  🔗 API Endpoints:                                             │
│  • POST /tracking/log-search/ - Record search query            │
│  • POST /tracking/log-view/ - Record product click             │
│  • GET /tracking/stats/ - Fetch overall analytics data         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🐰 MESSAGE BROKER ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  🐰 RABBITMQ - Event-Driven Communication                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 Functions:                                                  │
│  • Asynchronous event publishing & consumption                │
│  • Service decoupling & loose coupling                        │
│  • Saga pattern implementation                                │
│  • Event sourcing & CQRS support                             │
│  • Dead letter queue for failed messages                     │
│                                                                 │
│  🔄 Event Flow:                                               │
│                                                                 │
│  🔐 Auth Service                                               │
│        ↓ (customer_created, customer_updated)                  │
│  📤 Auth Publisher                                             │
│        ↓                                                       │
│  🐰 RabbitMQ Exchange                                          │
│        ↓                                                       │
│  📥 Customer Consumer                                          │
│        ↓                                                       │
│  👥 Customer Service Database                                  │
│                                                                 │
│  📊 Event Types:                                               │
│  • customer_created - New customer registration               │
│  • customer_updated - Customer profile changes                │
│  • order_placed - New order events                           │
│  • payment_processed - Payment confirmations                  │
│  • inventory_updated - Stock level changes                    │
│                                                                 │
│  🔧 Configuration:                                             │
│  • Port: 5672 (AMQP), 15672 (Management UI)                  │
│  • Durability: Persistent queues & messages                   │
│  • Acknowledgments: Manual ack for reliability                │
│  • Dead Letter Queue: Failed message handling                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ DATABASE ARCHITECTURE

```
PostgreSQL Cluster - 11 Dedicated Databases

┌─────────────────────────────────────────────────────────────────┐
│  🗃️ DATABASE DISTRIBUTION                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔐 auth_db (:5432)                                            │
│  • customers, staff, outbox_events                            │
│                                                                 │
│  👥 customer_db (:5433)                                        │
│  • customers, shipping_addresses                              │
│                                                                 │
│  👨‍💼 staff_db (:5434)                                        │
│  • staff, staff_sessions                                      │
│                                                                 │
│  📦 product_db (:5437)                                         │
│  • products (catalog, stock, supplier_id)                     │
│                                                                 │
│  🛒 cart_db (:5436)                                            │
│  • cart_items (customer_id, product_type, product_id, qty)    │
│                                                                 │
│  📦 order_db (:5438)                                           │
│  • orders, order_items (order lifecycle & fulfillment)       │
│                                                                 │
│  💳 payment_db (:5439)                                         │
│  • payments, payment_methods (transactions & gateways)        │
│                                                                 │
│  🎟️ voucher_db (:5440)                                         │
│  • vouchers, voucher_usage (discounts & campaigns)            │
│                                                                 │
│  ⭐ rating_db (:5441)                                          │
│  • ratings (reviews, stars, sentiment analysis)              │
│                                                                 │
│  🏭 supplier_db (:5442)                                        │
│  • suppliers (vendor management & supply chain)               │
│                                                                 │
│  📦 Distributed Category DBs (:5451 - :5460)                   │
│  • book_db, clothes_db, laptop_db, phone_db, tablet_db,       │
│  • camera_db, headphone_db, watch_db, shoe_db, furniture_db   │
│                                                                 │
│  💎 Qdrant Vector Storage (:6333)                              │
│  • High-dimensional embeddings for recommendation search       │
│                                                                 │
│  🔒 Security Features:                                         │
│  • Individual user credentials per service                    │
│  • Network isolation via Docker networks                      │
│  • Encrypted connections (SSL/TLS)                           │
│  • Backup & recovery procedures                              │
│  • Connection pooling & optimization                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

```
Docker Compose Orchestration

┌─────────────────────────────────────────────────────────────────┐
│  🐳 CONTAINERIZATION STRATEGY                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📦 Service Containers:                                        │
│  • api-gateway        (Django + Gunicorn)                     │
│  • auth-service       (Django + PostgreSQL client)           │
│  • customer-service   (Django + RabbitMQ consumer)            │
│  • staff-service      (Django + Admin interface)             │
│  • product-service    (Django + Unified catalog)              │
│  • cart-service       (Django + Session management)           │
│  • order-service      (Django + Workflow orchestration)      │
│  • payment-service    (Django + Gateway integrations)        │
│  • voucher-service    (Django + Campaign management)          │
│  • rating-service     (Django + Sentiment analysis)          │
│  • supplier-service   (Django + Supply chain)                │
│                                                                 │
│  🗄️ Database Containers:                                       │
│  • auth-db, customer-db, staff-db                            │
│  • product-db, cart-db, order-db                             │
│  • payment-db, voucher-db, rating-db                         │
│  • supplier-db                                               │
│                                                                 │
│  🐰 Message Broker:                                           │
│  • rabbitmq (Event-driven communication)                     │
│                                                                 │
│  🌐 Networking:                                               │
│  • Custom bridge network for service discovery               │
│  • Internal DNS resolution                                   │
│  • Port mapping for external access                          │
│  • Load balancing via API Gateway                            │
│                                                                 │
│  📁 Volume Management:                                         │
│  • Persistent data volumes for databases                     │
│  • Shared volumes for static files                           │
│  • Log aggregation volumes                                   │
│                                                                 │
│  🔧 Environment Configuration:                                 │
│  • Environment-specific settings                             │
│  • Secret management for credentials                         │
│  • Health checks & monitoring                                │
│  • Auto-restart policies                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 SYSTEM WORKFLOWS

### 🛍️ **Customer Purchase Journey**
```
🔄 CUSTOMER PURCHASE FLOW

    👤 Customer
       ↓ (Register/Login)
    🔐 Auth Service → JWT Token
       ↓
    🌐 API Gateway → Route requests
       ↓
     📦 Browse Products (Unified Catalog)
       ↓ (Add to Cart)
    🛒 Cart Service → Manage items
       ↓ (Apply Voucher)
    🎟️ Voucher Service → Validate & apply discount
       ↓ (Checkout)
    📦 Order Service → Create order
       ↓ (Process Payment)
    💳 Payment Service → Handle transaction
       ↓ (Confirm Order)
    📧 Notification → Customer confirmation
       ↓ (Fulfillment)
    🚚 Shipping → Order delivery
       ↓ (Post-Purchase)
     ⭐ Rating Service → Collect feedback
```

### 👨‍💼 **Staff Management Workflow**
```
🔄 STAFF MANAGEMENT FLOW

    👨‍💼 Staff Login
       ↓ (Authentication)
    🔐 Auth Service → Verify role & permissions
       ↓
    🌐 API Gateway → Admin routes
       ↓
    📊 Staff Dashboard → Analytics & KPIs
       ↓ (Product Management)
    📚 Book/Clothes Service → CRUD operations
       ↓ (Supplier Management)
    🏭 Supplier Service → Vendor relationships
       ↓ (Order Processing)
    📦 Order Service → Fulfillment management
       ↓ (Customer Support)
    🤖 Chatbot Service → Monitor AI performance
```

```

---

## 📊 SYSTEM METRICS & PERFORMANCE

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 PERFORMANCE SPECIFICATIONS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🚀 Response Times:                                            │
│  • API Gateway routing: < 10ms                                │
│  • Authentication: < 50ms                                     │
│  • Product catalog: < 100ms                                   │
│  • Cart operations: < 50ms                                    │
│  • Order processing: < 200ms                                  │
│  • Payment processing: < 3s                                   │
│  • AI Chatbot (RAG): < 100ms (cached), < 500ms (first query) │
│                                                                 │
│  💾 Memory Usage:                                              │
│  • Each microservice: ~50-100MB                               │
│  • PostgreSQL databases: ~100-200MB each                      │
│  • RabbitMQ: ~50MB                                           │
│  • AI Model (BERT): ~120MB                                   │
│  • Total system: ~2-3GB                                      │
│                                                                 │
│  🔄 Throughput:                                               │
│  • API requests: 1000+ req/sec                               │
│  • Database connections: 100+ concurrent                      │
│  • Message processing: 500+ events/sec                        │
│  • AI chatbot queries: 50+ queries/sec                       │
│                                                                 │
│  📈 Scalability:                                              │
│  • Horizontal scaling via container replication              │
│  • Database read replicas for performance                    │
│  • Load balancing across service instances                   │
│  • Auto-scaling based on resource utilization               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔒 SECURITY ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  🔒 SECURITY FRAMEWORK                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔐 Authentication & Authorization:                            │
│  • JWT-based authentication                                   │
│  • Role-based access control (Customer, Staff, Admin)        │
│  • Session management & token expiration                      │
│  • Password hashing with PBKDF2                              │
│                                                                 │
│  🌐 Network Security:                                          │
│  • Docker network isolation                                   │
│  • Service-to-service authentication                          │
│  • CORS configuration for web security                       │
│  • Rate limiting & DDoS protection                           │
│                                                                 │
│  🗄️ Data Security:                                            │
│  • Database connection encryption (SSL/TLS)                  │
│  • Sensitive data tokenization                               │
│  • PCI compliance for payment processing                     │
│  • Regular security audits                                   │
│                                                                 │
│  🛡️ Application Security:                                      │
│  • Input validation & sanitization                           │
│  • SQL injection prevention                                  │
│  • XSS protection                                           │
│  • CSRF token validation                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 TECHNOLOGY STACK SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│  🛠️ TECHNOLOGY STACK                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🐍 Backend Framework:                                         │
│  • Django 4.2 + Django REST Framework                        │
│  • Python 3.11                                               │
│                                                                 │
│  🗄️ Database:                                                 │
│  • PostgreSQL 15 (12 separate databases)                     │
│  • Connection pooling & optimization                         │
│                                                                 │
│  🐰 Message Broker:                                           │
│  • RabbitMQ 3.12 with Management UI                          │
│  • AMQP protocol for reliable messaging                      │
│                                                                 │
│  🤖 AI & Machine Learning:                                    │
│  • BERT Multilingual (sentiment analysis)                    │
│  • Sentence Transformers (all-MiniLM-L6-v2)                 │
│  • RAG (Retrieval-Augmented Generation)                      │
│                                                                 │
│  🌐 Frontend:                                                 │
│  • Django Templates + JavaScript                             │
│  • Bootstrap CSS Framework                                   │
│  • Real-time chat widget                                    │
│                                                                 │
│  🐳 Infrastructure:                                           │
│  • Docker & Docker Compose                                   │
│  • Multi-stage builds for optimization                       │
│  • Health checks & monitoring                               │
│                                                                 │
│  🔧 Development Tools:                                         │
│  • Git version control                                       │
│  • Environment-based configuration                           │
│  • Automated testing frameworks                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 DOCUMENTATION REFERENCES

- **📁 agent.md** - Complete project documentation with Phase 8 updates
- **🤖 AI_CHATBOT_WITH_RAG.md** - Detailed AI implementation guide
- **🚀 quick_start.sh** - One-command deployment script
- **🧪 test_chatbot.sh** - Automated testing script
- **🐳 docker-compose.yml** - Container orchestration configuration
- **📖 HUONG_DAN_DAY_DU.md** - Vietnamese documentation

---

```
╔══════════════════════════════════════════════════════════════════════════╗
║                               🎉 STATUS                                 ║
║                          IMPLEMENTATION: 100%                           ║
║                        AI CHATBOT WITH RAG: ✅                          ║
║                        PRODUCTION READY: ✅                             ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**Quick Start**: `./quick_start.sh`  
**Access**: http://localhost:8000 (Click 💬 to chat with AI!)  
**Admin**: http://localhost:15672 (RabbitMQ Management UI)

---

*Last Updated: 2026-04-06 | Phase 8 Complete | AI-Powered E-Commerce System*
