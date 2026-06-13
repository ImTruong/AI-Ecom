# Full luong AI, Embedding, Qdrant, Neo4j trong TruongShop

Tai lieu nay giai thich tu dau den cuoi cac phan lien quan AI trong repo: du lieu tu dau ra, seed vao Postgres nhu the nao, dua vao Qdrant/Neo4j qua dau, runtime request chay qua service nao, Neo4j duoc query ra sao, Qdrant embedding/search ra sao, GRU model tham gia luc nao, chatbot dung nhung nguon nao.

## 1. Tom tat sieu ngan

He thong AI co 4 cum chinh:

1. **Qdrant product vector search**
   - Du lieu nguon: product catalog tu `product-service`.
   - File build index: `services/vector_service/main.py`.
   - Model embedding: `SentenceTransformer('all-MiniLM-L6-v2')`, vector 384 chieu, cosine distance.
   - Output: collection Qdrant ten `products`.
   - Runtime search semantic: `services/vector_service/search_server.py`, endpoint `/api/recommendations/search`.

2. **Neo4j knowledge/behavior graph**
   - Du lieu nguon: cac PostgreSQL nghiep vu da seed: `auth_db`, `product_db`, `voucher_db`, `tracking_db`.
   - File seed Postgres tu CSV: `services/knowledge_service/db_seeder.py`.
   - File sync cart/order tu tracking: `services/knowledge_service/sync_operational_db.py`.
   - File import Postgres sang Neo4j: `services/knowledge_service/importer.py`.
   - Graph co cac node chinh: `User`, `Product`, `Category`, `Voucher`, `Search`.
   - Relationship chinh: `VIEWED`, `ADDED_TO_CART`, `CART_ACTION`, `BOUGHT`, `SEARCHED`, `BELONGS_TO`.

3. **Recommendation service**
   - File runtime: `services/recommendation_service/main.py`.
   - Endpoint ca nhan hoa: `/api/recommendations/{user_id}`.
   - Lay history tu cart/order/tracking API, lay candidate tu Neo4j, lay semantic context tu Qdrant, roi cham diem bang GRU neu model load duoc.
   - Model GRU: `/app/AI/new/GRU_best_model.h5`.
   - Encoders: `/app/AI/new/encoders.pkl`.

4. **Chatbot/RAG**
   - File container dang chay: `services/chatbot_service/main.py`.
   - Endpoint: `/api/chatbot/ask`.
   - Dung Qdrant de tim product theo message, dung Postgres `chatbot_db.knowledge_bases` de tim policy/FAQ bang keyword, dung Neo4j de lay history/product/voucher, dung GRU de rank candidate, dung Gemini neu co `GEMINI_API_KEY`, neu khong fallback sang local template.

## 2. Ban do service va port

Trong `docker-compose.yml`:

- `qdrant` o lines 435-445:
  - HTTP API: host `localhost:6333`, trong Docker network la `qdrant:6333`.
  - Volume: `qdrant_data`.

- `neo4j` o lines 447-464:
  - Browser: `localhost:7474`.
  - Bolt: `localhost:7687`, trong Docker network la `bolt://neo4j:7687`.
  - `NEO4J_AUTH=none`, auth disabled, nhung code van truyen user/password o nhieu noi. Vi auth tat nen van connect duoc.
  - Volume: `neo4j_data`.

- `recommendation-service` o lines 466-502:
  - Container port `8001`, expose ra host `8101`.
  - Ket noi Neo4j qua `NEO4J_URI=bolt://neo4j:7687`.
  - Biet Qdrant qua `QDRANT_HOST=qdrant`, `QDRANT_PORT=6333`.
  - Biet semantic search service qua `RECOMMENDATION_SEARCH_SERVICE_URL=http://recommendation-search-service:8002`.
  - Mount model `./AI/new:/app/AI/new:ro`.

- `knowledge-service` o lines 504-529:
  - Container port `8005`, expose ra host `8105`.
  - Co env URL toi `product_db`, `voucher_db`, `tracking_db`, `auth_db`.
  - Mount `./AI/data:/AI/data`, day la CSV source cho `db_seeder.py`.

- `chatbot-service` o lines 531-555:
  - Container port `8000`, expose ra host `8012`.
  - Dung `chatbot_db`, Neo4j, Gemini key.
  - Mount model `./AI/new:/app/AI/new:ro`.

- `vector-service` o lines 557-571:
  - Profile `manual`, khong chay mac dinh neu chi `docker compose up`.
  - Chay de build lai Qdrant index.

- `recommendation-search-service` o lines 573-594:
  - Profile `manual`.
  - Reuse image vector service, nhung command la `python /search_server.py`.
  - Container port `8002`, expose host `8102`.
  - Day moi la API semantic search runtime that su goi Qdrant bang embedding query.

API Gateway route AI o `services/api_gateway/gateway/middleware.py`:

- `/api/recommendations/search` -> `recommendation-search-service` lines 60-63.
- `/api/recommendations/` -> `recommendation-service` lines 64-67.
- `/api/chatbot/` -> `chatbot-service` lines 68-70.

Thu tu route rat quan trong: `/api/recommendations/search` dung prefix rieng dat truoc `/api/recommendations/`, nen request search se di sang semantic search service, khong di vao recommendation service.

## 3. Quick start chay AI theo thu tu nao

File `quick_start.sh` la flow khoi tao tong:

1. Lines 72-75: migrate tat ca Django service.
2. Lines 77-83: seed du lieu:
   - `knowledge-service python db_seeder.py`
   - `knowledge-service python sync_operational_db.py`
   - `voucher-service python seed_vouchers.py`
   - `user-service python seed_roles.py`
   - `user-service python seed_users.py`
3. Lines 85-88: build Qdrant product vector index:
   - `docker compose --profile manual run --rm --build vector-service`
   - `docker compose --profile manual up -d recommendation-search-service`
4. Lines 90-92: import knowledge graph vao Neo4j:
   - `knowledge-service python importer.py`
5. Lines 94-106: check recommendation service `/health` va sample `/api/recommendations/0?limit=10`.

Noi cach khac:

```text
CSV trong AI/data
  -> db_seeder.py
  -> PostgreSQL nghiep vu
  -> sync_operational_db.py bo sung cart/order tu tracking
  -> vector_service/main.py lay product qua product-service de upsert Qdrant
  -> importer.py lay Postgres sang Neo4j
  -> recommendation/chatbot/gateway runtime doc Qdrant + Neo4j
```

## 4. Du lieu goc nam o dau

Nguon du lieu AI/dataset trong repo:

- `AI/data/customer.csv`: customer/user.
- `AI/data/address.csv`: dia chi.
- `AI/data/categories.csv`: category.
- `AI/data/products.csv`: product.
- `AI/data/product_variants.csv`: variant.
- `AI/data/attributes.csv`, `attribute_values.csv`, `product_variant_options.csv`: thuoc tinh bien the.
- `AI/data/product_views.csv`: hanh vi xem product.
- `AI/data/cart_actions.csv`: hanh vi gio hang.
- `AI/data/purchase_actions.csv`: hanh vi mua hang.
- `AI/data/tracking_events.csv`: tracking event tong quat.
- `data_user500.csv`: file interaction cu/bo sung. Trong luong hien tai bi comment khi import Neo4j.
- `AI/new/GRU_best_model.h5`: model GRU runtime.
- `AI/new/encoders.pkl`: encoder de bien `behavior`, `item`, `category` thanh integer cho GRU.
- `AI/new/model_results.csv`: ket qua model.

## 5. Seed CSV vao PostgreSQL

File chinh: `services/knowledge_service/db_seeder.py`.

`db_seeder.py` khong seed Neo4j truc tiep. No seed cac PostgreSQL nghiep vu:

- `auth_db`: bang `"user"` va `address`.
- `product_db`: `categories`, `products`, `attributes`, `attribute_values`, `product_variants`, `product_variant_options`.
- `tracking_db`: `product_views`, `cart_actions`, `purchase_actions`, `tracking_events`.

Flow:

1. `truncate_tables()` xoa data cu trong cac bang Postgres.
2. `seed_auth()`:
   - Doc `/AI/data/customer.csv`.
   - Insert vao `"user"`.
   - Doc `/AI/data/address.csv`.
   - Insert vao `address`.
3. `seed_product()`:
   - Doc categories/products/attributes/variants.
   - Co logic de-duplicate:
     - category trung ten se map ve primary category.
     - product trung clean name se map ve primary product.
     - variant cua product duplicate se map ve primary variant.
   - Quan trong: `product_map` va `variant_map` duoc tao de tracking sau nay tro dung product/variant da dedupe.
4. `seed_tracking()`:
   - Doc `product_views.csv`, `cart_actions.csv`, `purchase_actions.csv`, `tracking_events.csv`.
   - Map `product_id` qua `product_map`.
   - Map `product_variant_id` qua `variant_map`.
   - Insert vao tracking_db.
5. `reset_sequences()` set lai sequence id.

Sau `db_seeder.py`, Postgres moi la source-of-truth runtime cho product/tracking/user.

## 6. Sync operational DB tu tracking

File: `services/knowledge_service/sync_operational_db.py`.

Script nay tao trang thai gio hang va don hang tu log tracking:

1. Doc product/variant tu `product_db`.
2. Doc user/address tu `auth_db`.
3. Doc `cart_actions` va `purchase_actions` tu `tracking_db`.
4. Simulate cart theo thoi gian:
   - `cart add` thi tang quantity.
   - `remove/delete` thi xoa item.
   - khi co purchase thi bo item da mua khoi active cart.
5. Truncate `cart_db` va `order_db`.
6. Insert active carts vao `cart_db`.
7. Insert delivered orders + order items + ship tracking vao `order_db`.

Script nay khong dung Qdrant/Neo4j truc tiep, nhung no quan trong vi recommendation service runtime se lay current cart tu `cart-service` va recent orders tu `order-service`.

## 7. Qdrant: insert product vectors qua dau

File build index: `services/vector_service/main.py`.

### 7.1. Input cua Qdrant la gi

Config o lines 8-12:

- `PRODUCT_SERVICE_URL`, default `http://product-service:8000/api/products/`.
- `QDRANT_HOST`, default `qdrant`.
- `QDRANT_PORT`, default `6333`.
- collection hard-code: `products`.

Function `fetch_products()` lines 14-27 goi HTTP GET toi product-service de lay list product JSON.

Vay du lieu Qdrant khong doc CSV truc tiep. No lay product da seed trong `product_db`, thong qua API `product-service`.

### 7.2. Text nao duoc dem di embedding

Function `format_product_text(p)` lines 29-69 ghep mot chuoi text tu:

- Product Name
- Category
- Type/product_type
- Description
- Attributes neu la dict
- Variants neu la list
- Cac field khac neu khong nam trong `skip_keys`

Vi du logical:

```text
Product Name: iPhone 15. Category: Phones. Type: electronic.
Description: ...
Attributes: storage: 128GB, color: black.
Options: Black 128GB, Blue 256GB.
```

Chuoi nay duoc luu lai vao payload field `raw_text`, nen luc search co the enrich hoac keyword fallback.

### 7.3. Embedding model va vector schema

Trong `main()`:

- Lines 74-76: load `SentenceTransformer('all-MiniLM-L6-v2')`.
- Model nay output vector 384 chieu.
- Lines 86-91: neu collection `products` chua co thi tao:
  - `VectorParams(size=384, distance=Distance.COSINE)`.

### 7.4. Upsert point vao Qdrant

Loop lines 101-122:

- Moi product:
  - `text = format_product_text(p)`.
  - `vector = model.encode(text).tolist()`.
  - Tao `PointStruct`:
    - `id = p['id']`.
    - `vector = vector`.
    - `payload` gom `id`, `name`, `category`, `product_type`, `price`, `image_url`, `raw_text`.

Lines 124-129 goi:

```python
client.upsert(collection_name="products", points=points)
```

Nghia la Qdrant collection `products` co 1 point/product, point id bang product id.

### 7.5. Khi nao index Qdrant duoc build

`quick_start.sh` lines 85-88 chay `vector-service` manual:

```bash
docker compose --profile manual run --rm --build vector-service
docker compose --profile manual up -d recommendation-search-service
```

`fast_reload.sh` cung rebuild vector index sau khi rebuild services.

Luu y: `vector-service` la job build/sync. Chay xong no thoat. `recommendation-search-service` moi la server search runtime.

## 8. Qdrant: runtime search chay nhu the nao

File runtime: `services/vector_service/search_server.py`.

### 8.1. Khoi tao

Lines 12-17 config:

- `PRODUCT_SERVICE_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`
- `COLLECTION_NAME`, default `products`
- `EMBEDDING_MODEL`, default `all-MiniLM-L6-v2`
- `PORT`, default `8002`

Lines 19-20 tao:

- `QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)`
- `SentenceTransformer(EMBEDDING_MODEL)`

### 8.2. Endpoint search

Class `SearchHandler`, lines 98-158:

- `/health` tra ve service health.
- `/api/recommendations/search` moi la endpoint search.

Flow request:

1. Lines 108-111 doc query string:
   - `query`
   - `limit`, clamp 1..30
2. Line 117: `vector = embedding_model.encode(query).tolist()`.
3. Line 118: `results = qdrant_search(vector, limit)`.
4. `qdrant_search()` lines 23-48 goi Qdrant search voi:
   - collection `products`
   - query_vector la embedding cua user query
   - with_payload true
5. Line 119 goi `fetch_products()` de enrich payload tu product-service. Neu product-service fail thi dung payload trong Qdrant.
6. Lines 121-132 map thanh response:
   - `id`
   - `score`
   - `payload`
   - `source: "qdrant"`
   - `reason: "Semantic vector search via Qdrant"`
7. Lines 133-139 return strategy `qdrant_semantic_search`.

### 8.3. Ai goi endpoint nay

1. Gateway search page:
   - `services/api_gateway/templates/search.html` lines 25-44 goi `/api/recommendations/search?query=...`.
   - Gateway route sang `recommendation-search-service` theo middleware lines 60-63.

2. Recommendation service:
   - `services/recommendation_service/main.py` function `_qdrant_context_recommendations()` lines 488-539 goi `RECOMMENDATION_SEARCH_SERVICE_URL/api/recommendations/search`.
   - Query khong phai raw user keyword, ma la context text tu history/cart/purchase.

3. Chatbot:
   - `services/chatbot_service/main.py` function `qdrant_semantic_search()` lines 173-183 goi `http://recommendation-search-service:8002/api/recommendations/search`.
   - Trong `/api/chatbot/ask`, lines 236-241 dung user message de lay product semantic matches.

### 8.4. Luu y de khong nham

Trong `services/recommendation_service/main.py` cung co endpoint `/api/recommendations/search` lines 341-364, nhung gateway hien route `/api/recommendations/search` sang `recommendation-search-service`, khong sang `recommendation-service`.

Endpoint search trong recommendation-service dung `VectorSearchClient` lines 195-252, nhung class nay khong embedding query; no scroll points tu Qdrant roi keyword-score tren payload. Do gateway route hien tai, duong nay thuong khong phai duong UI search chinh.

## 9. Neo4j: import graph vao dau

File import graph: `services/knowledge_service/importer.py`.

### 9.1. Ket noi va clear graph

Class `KnowledgeImporter`:

- Lines 9-12: tao `GraphDatabase.driver(uri, auth=auth)`.
- Lines 17-20: `clear_database()` chay:

```cypher
MATCH (n) DETACH DELETE n
```

Vay moi lan `importer.py` chay trong quick start/update, graph bi xoa het roi import lai tu Postgres.

### 9.2. Constraint

Lines 22-27 tao unique constraints:

```cypher
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE
CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE
CREATE CONSTRAINT voucher_id IF NOT EXISTS FOR (v:Voucher) REQUIRE v.id IS UNIQUE
```

### 9.3. Import CSV interaction cu

Function `import_data(csv_path)` lines 29-88 co the doc `data_user500.csv` va tao:

- `(u:User)-[:VIEWED]->(p:Product)`
- `(u:User)-[:SEARCHED]->(p:Product)`
- `(u:User)-[:ADDED_TO_CART]->(p:Product)`
- `(u:User)-[:SEARCHED]->(s:Search)`

Nhung trong `__main__`, line 316 dang comment:

```python
# importer.import_data("/data_user500.csv")
```

Nen quick start hien tai khong import truc tiep `data_user500.csv` vao Neo4j. Thay vao do import tu Postgres.

### 9.4. Import users tu auth_db

`import_users_from_db()` lines 287-309:

- Query Postgres:

```sql
SELECT id, email, full_name FROM "user" WHERE role = 'customer'
```

- Tao/cap nhat node:

```cypher
MERGE (u:User {id: $uid})
SET u.email = $email,
    u.full_name = $full_name
```

### 9.5. Import products/categories tu product_db

`import_products_from_db()` lines 150-191:

- Fetch categories lines 102-105:

```sql
SELECT id, name, description, icon FROM categories
```

- Fetch products lines 107-114:

```sql
SELECT id, name, description, price, image_url, product_type, attributes, category_id, is_active
FROM products
WHERE is_active = TRUE
```

- Category node lines 166-172:

```cypher
MERGE (c:Category {id: $id})
SET c.name = $name,
    c.description = $desc,
    c.icon = $icon
```

- Product node + relationship category lines 174-191:

```cypher
MERGE (p:Product {id: $id})
SET p.name = $name,
    p.description = $desc,
    p.price = $price,
    p.image_url = $image_url,
    p.product_type = $ptype,
    p.attributes = $attrs,
    p.is_active = $is_active
WITH p
MATCH (c:Category {id: $category_id})
MERGE (p)-[:BELONGS_TO]->(c)
```

### 9.6. Import vouchers tu voucher_db

`import_vouchers_from_db()` lines 193-227:

- Fetch vouchers active lines 116-124.
- Tao node:

```cypher
MERGE (v:Voucher {id: $id})
SET v.code = $code,
    v.name = $name,
    v.description = $desc,
    v.discount_type = $dtype,
    v.discount_value = $dvalue,
    v.min_order_value = $min_value,
    v.max_discount = $max_discount,
    v.end_date = $end_date,
    v.is_global = $is_global,
    v.is_active = $is_active
```

Voucher hien chi la node doc lap, chua co relation toi Product/Category/User.

### 9.7. Import tracking tu tracking_db

`import_tracking_from_db()` lines 229-285:

Fetch tu Postgres:

- `product_views`: lines 126-129.
- `cart_actions`: lines 131-134.
- `purchase_actions`: lines 136-139.
- `search_history`: lines 141-148. Neu bang khong ton tai thi rollback va bo qua.

Tao graph:

1. View, lines 247-255:

```cypher
MERGE (u:User {id: $uid})
WITH u
MATCH (p:Product {id: $pid})
MERGE (u)-[r:VIEWED {timestamp: $ts}]->(p)
```

2. Cart, lines 257-266:

```python
rel = "ADDED_TO_CART" if action_type == "add" else "CART_ACTION"
```

Roi:

```cypher
MERGE (u:User {id: $uid})
WITH u
MATCH (p:Product {id: $pid})
MERGE (u)-[r:ADDED_TO_CART|CART_ACTION {timestamp: $ts}]->(p)
```

3. Purchase, lines 268-276:

```cypher
MERGE (u:User {id: $uid})
WITH u
MATCH (p:Product {id: $pid})
MERGE (u)-[r:BOUGHT {timestamp: $ts}]->(p)
```

4. Search query, lines 278-285:

```cypher
MERGE (u:User {id: $uid})
MERGE (s:Search {query: $search_query})
MERGE (u)-[r:SEARCHED {timestamp: $ts}]->(s)
```

### 9.8. Main importer chay nhung gi

Lines 311-322:

```python
importer.clear_database()
importer.create_constraints()
# importer.import_data("/data_user500.csv")
importer.import_users_from_db(os.getenv("USER_DATABASE_URL"))
importer.import_products_from_db(os.getenv("PRODUCT_DATABASE_URL"))
importer.import_vouchers_from_db(os.getenv("VOUCHER_DATABASE_URL"))
importer.import_tracking_from_db(os.getenv("TRACKING_DATABASE_URL"))
```

Graph sau khi import se co:

```text
(User {id,email,full_name})
(Product {id,name,description,price,image_url,product_type,attributes,is_active})
(Category {id,name,description,icon})
(Voucher {id,code,name,description,discount_type,discount_value,...})
(Search {query})

(Product)-[:BELONGS_TO]->(Category)
(User)-[:VIEWED {timestamp}]->(Product)
(User)-[:ADDED_TO_CART {timestamp}]->(Product)
(User)-[:CART_ACTION {timestamp}]->(Product)
(User)-[:BOUGHT {timestamp}]->(Product)
(User)-[:SEARCHED {timestamp}]->(Search)
```

## 10. Neo4j duoc query luc runtime nhu the nao

Co 3 noi query Neo4j chinh:

1. `services/recommendation_service/main.py`: GraphClient cho recommendation.
2. `services/chatbot_service/chatbot_app/kb_client.py`: KBClient cho chatbot.
3. `services/knowledge_service/main.py`: service FastAPI nho, co endpoint graph recommendation/path, nhung khong thay gateway route toi no.

### 10.1. Recommendation service query Neo4j

File: `services/recommendation_service/main.py`.

`GraphClient` ket noi Neo4j lines 92-98.

#### Popular products

Function `popular_products()` lines 122-143:

```cypher
MATCH (p:Product)
WHERE coalesce(p.is_active, true) = true AND NOT p.id IN $excluded_ids
OPTIONAL MATCH (:User)-[b:BOUGHT]->(p)
OPTIONAL MATCH (:User)-[c:ADDED_TO_CART]->(p)
OPTIONAL MATCH (:User)-[v:VIEWED]->(p)
WITH p, count(DISTINCT b) AS buys, count(DISTINCT c) AS carts, count(DISTINCT v) AS views
RETURN p.id AS id,
       (buys * 3.0 + carts * 2.0 + views) AS graph_score,
       'popular' AS source,
       buys, carts, views
ORDER BY graph_score DESC, p.id ASC
LIMIT $limit
```

Logic:

- Moi buy nang 3 diem.
- Moi add-to-cart nang 2 diem.
- Moi view nang 1 diem.
- San pham active va khong nam trong excluded.
- Dung khi user moi khong co history, hoac fallback khi candidate rong.

#### Related products theo other users

Function `_related_products()` lines 145-192:

```cypher
MATCH (other:User)-[seed_action:ADDED_TO_CART]->(seed:Product)
WHERE seed.id IN $seed_ids AND other.id <> $user_id
MATCH (other)-[target:{rel_type}]->(p:Product)
WHERE coalesce(p.is_active, true) = true
  AND NOT p.id IN $seed_ids
  AND NOT p.id IN $excluded_ids
  AND (
    seed_action.timestamp IS NULL
    OR target.timestamp IS NULL
    OR toString(target.timestamp) >= toString(seed_action.timestamp)
  )
WITH p, count(DISTINCT other) AS users, count(target) AS interactions
RETURN p.id AS id,
       (users * $weight + interactions) AS graph_score,
       $source AS source,
       users,
       interactions
ORDER BY graph_score DESC, users DESC, p.id ASC
LIMIT $limit
```

`fetch_candidates()` lines 100-120 goi `_related_products()` 3 lan voi:

- `BOUGHT`, weight 3.0, source `other_users_bought`.
- `ADDED_TO_CART`, weight 2.0, source `other_users_added_to_cart`.
- `VIEWED`, weight 1.0, source `other_users_viewed`.

Y nghia:

- Lay `seed_ids` la product user hien tai da tuong tac.
- Tim user khac da add-to-cart cac seed product.
- Xem sau do ho bought/cart/view product nao khac.
- Product do tro thanh candidate.

Luu y rat quan trong: query luon match `seed_action:ADDED_TO_CART` cho seed, du `rel_type` target la BOUGHT/VIEWED. Nghia la graph recommendation uu tien "nguoi khac da them cung mon vao gio" hon la bat ky relation seed nao.

### 10.2. Chatbot KBClient query Neo4j

File: `services/chatbot_service/chatbot_app/kb_client.py`.

`get_user_history()` lines 20-33:

```cypher
MATCH (u:User {id: $user_id})-[r]->(p:Product)
WHERE type(r) CONTAINS 'VIEW' OR type(r) CONTAINS 'CART' OR type(r) CONTAINS 'SEARCH'
OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
RETURN p.id as product_id, p.name as name, type(r) as action,
       COALESCE(c.name, 'Chưa phân loại') as category, c.id as category_id
ORDER BY r.timestamp DESC LIMIT 10
```

Luu y:

- Query nay chi lay relationship toi `Product`.
- Neu `SEARCHED` relationship la `(User)-[:SEARCHED]->(Search)` thi khong match vi node target khong phai Product.
- `BOUGHT` khong duoc lay vi WHERE chi co VIEW/CART/SEARCH, khong co BOUGHT.

`get_product_details()` lines 35-47:

- Lay detail product theo id, join category.

`get_top_rated_products()` lines 49-62:

- Query Product order by `rating`.
- Nhung importer khong set `p.rating`, nen `COALESCE(p.rating, 0.0)` se thanh 0 cho tat ca neu khong co nguon rating khac. Luc do order chu yeu khong that su "top rated".

`get_active_vouchers()` lines 64-75:

- Lay node Voucher active.

`search_products()` lines 77-90:

- Search Neo4j bang substring:

```cypher
MATCH (p:Product)
WHERE p.name CONTAINS $keyword OR EXISTS {
    MATCH (p)-[:BELONGS_TO]->(c:Category)
    WHERE c.name CONTAINS $keyword
}
RETURN p.id as id, p.name as name, p.price as price
LIMIT $limit
```

`record_user_action()` lines 92-107:

- Map trigger:
  - `VIEW` -> `VIEWED`
  - `SEARCH` -> `SEARCHED`
  - `CART` -> `ADDED_TO_CART`
- Roi ghi:

```cypher
MERGE (u:User {id: $user_id})
WITH u
MATCH (p:Product {id: $product_id})
MERGE (u)-[r:REL_TYPE {timestamp: timestamp()}]->(p)
```

Luu y: `timestamp()` cua Neo4j la temporal object, trong khi importer tu Postgres co the la datetime/string. Cac query recommendation co ep `toString()`.

## 11. Recommendation service: full luong endpoint `/api/recommendations/{user_id}`

File: `services/recommendation_service/main.py`.

Endpoint lines 367-450.

### 11.1. Request tu UI den service

Homepage:

- `services/api_gateway/templates/homepage.html` lines 220-248 goi:

```javascript
fetch(`/api/recommendations/${userId}?limit=10&_=${Date.now()}`, { headers, cache: 'no-store' })
```

Cart:

- `services/api_gateway/templates/cart.html` lines 456-489 goi cung endpoint.

Gateway:

- `services/api_gateway/gateway/middleware.py` lines 64-67 route `/api/recommendations/` sang `recommendation-service:8001`.

### 11.2. Build user history

Endpoint line 375:

```python
history = _build_user_history(user_id, authorization)
```

Function `_build_user_history()` lines 464-485 gom 3 nguon:

1. `_fetch_current_cart_signals(authorization)` lines 571-581:
   - Goi `CART_SERVICE_URL`.
   - Can Authorization header.
   - Tao `ProductSignal(product_id, "cart", timestamp, "cart")`.

2. `_fetch_recent_purchase_signals(authorization)` lines 584-595:
   - Goi `ORDER_SERVICE_URL + "mine/"`.
   - Can Authorization header.
   - Tao `ProductSignal(product_id, "buy", order.created_at, "purchase")`.

3. `_fetch_tracking_history(user_id)` lines 598-605:
   - Goi `TRACKING_SERVICE_URL + "user-history/{user_id}/"`.
   - Lay carts/purchases/views.
   - Map thanh behavior:
     - cart -> `cart`
     - purchase -> `buy`
     - view -> `pv`

Sau do:

- Merge tat ca signal.
- Deduplicate theo `(product_id, behavior, timestamp)`.
- Sort tang dan theo timestamp.
- Lay 20 behavior gan nhat (`SEQUENCE_LENGTH=20`).

### 11.3. Exclude product da co trong cart/purchase

Line 376:

```python
excluded_ids = {signal.product_id for signal in history if signal.source in {"cart", "purchase"}}
```

Muc dich: khong recommend lai mon user dang co trong cart hoac da mua gan day.

### 11.4. Neu khong co history

Lines 378-381:

- Goi `_popular_recommendations(limit)`.
- Strategy thanh `popular_for_new_user`.
- `_popular_recommendations()` lines 622-647 dung Neo4j popular query, neu fail thi fallback product-service.

### 11.5. Lay candidate tu Neo4j

Lines 383-388:

- `seed_ids = unique product ids tu history`.
- `candidates = graph_client.fetch_candidates(user_id, seed_ids, excluded_ids, CANDIDATE_LIMIT)`.
- Neu candidate it hon limit thi bo sung popular products.

Candidate co cac field:

- `id`
- `graph_score`
- `source`
- `users`
- `interactions`

### 11.6. Lay product details tu product-service

Line 393:

```python
product_map = product_client.get_product_map(set(candidate_ids) | {signal.product_id for signal in history})
```

ProductClient lines 69-89 goi `PRODUCT_SERVICE_URL` de lay full list products, roi filter theo id. Chi product co trong map moi duoc render payload day du.

### 11.7. Qdrant context chen len dau

Lines 394-399:

```python
qdrant_first = _qdrant_context_recommendations(...)
```

Function `_build_qdrant_context_text()` lines 542-553 tao context text tu history:

- `pv` lap 1 lan.
- `cart` lap 2 lan.
- `buy` lap 3 lan.

Vi du:

```text
Viewed: Product Name: A...
Added to cart: Product Name: B...
Added to cart: Product Name: B...
Purchased: Product Name: C...
Purchased: Product Name: C...
Purchased: Product Name: C...
```

Function `_qdrant_context_recommendations()` lines 488-539:

1. Goi `recommendation-search-service /api/recommendations/search`.
2. Truyen query la context text cat 1500 ky tu.
3. Lay semantic matches tu Qdrant.
4. Bo product trong excluded.
5. Gan source `qdrant_context`.
6. Return toi da `QDRANT_CONTEXT_LIMIT` item.

Trong response UI, source `qdrant_context` duoc hien badge `Semantic`:

- Homepage lines 261-265.
- Cart lines 501-505.

### 11.8. Cham diem bang GRU model

`PurchaseModel` lines 255-327:

- Load model lines 266-277:
  - `tf.keras.models.load_model(MODEL_PATH)`
  - `pickle.load(ENCODER_PATH)`
- `MODEL_PATH` default line 45: `/app/AI/new/GRU_best_model.h5`.
- `ENCODER_PATH` default line 46: `/app/AI/new/encoders.pkl`.

Prediction `predict()` lines 279-313:

Input:

- `history`: list `ProductSignal`.
- `products`: product_map.
- `target_id`: candidate product id.

Encode:

- target product id bang `item_encoder`, offset +1.
- Moi signal trong 20 item gan nhat:
  - behavior: `behavior_encoder`.
  - item id: `item_encoder`, offset +1.
  - category id: `category_encoder`, offset +1.
- Left pad ve length 20 bang 0.

Model input la 4 mang:

```python
[
  encoded_behaviors: shape (1, 20),
  encoded_items: shape (1, 20),
  encoded_categories: shape (1, 20),
  target_encoded: shape (1, 1),
]
```

Output:

- `float(self.model.predict(...)[0][0])`, hieu la probability/score user se mua target.

Endpoint lines 402-428:

- Sort candidates theo graph_score.
- Chi score toi da `MODEL_SCORE_LIMIT`.
- Moi candidate:
  - neu product excluded, da nam trong qdrant_first, hoac khong co product_map thi skip.
  - `model_score = purchase_model.predict(...)`.
  - `graph_score = raw_graph_score / max_graph_score`.
  - `final_score = model_score if model_score is not None else graph_score`.
- Sort theo `(score, graph_score)` giam dan.

Final recommendations lines 428-445:

```python
recommendations = (qdrant_first + scored)[:limit]
```

Tuc la semantic context tu Qdrant duoc uu tien dat truoc, sau do moi den graph/GRU scored items.

Response strategy:

```text
qdrant_context_then_cart_purchase_graph_gru
```

### 11.9. Fallback

- Neu model khong load duoc, `purchase_model.predict()` tra `None`, final score dung graph_score.
- Neu graph fail/rong, dung popular.
- Neu popular Neo4j khong co, fallback product-service.

## 12. Endpoint `/api/recommendations/search`

Duong UI search chinh:

```text
Browser search.html
  -> /api/recommendations/search?query=...
  -> API Gateway
  -> recommendation-search-service:8002
  -> services/vector_service/search_server.py
  -> embedding query
  -> Qdrant vector search collection products
  -> enrich product-service
  -> response recommendations
```

Search page:

- `services/api_gateway/templates/search.html` lines 25-44.
- Neu semantic response khong co product thi fallback `/api/products/?search=...`.

## 13. Chatbot: full luong `/api/chatbot/ask`

File container dang chay: `services/chatbot_service/main.py`.

Dockerfile `services/chatbot_service/Dockerfile` chay:

```dockerfile
CMD ["python", "main.py"]
```

Nen `chatbot_app/views.py` la luong Django cu/khac, khong phai luong container hien tai.

### 13.1. Startup tao custom KB table

Lines 43-65:

- Khi startup, `init_db()` tao table `knowledge_bases` trong `chatbot_db`.

Schema:

```sql
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

CRUD endpoints lines 80-169:

- GET `/api/chatbot/knowledge`
- POST `/api/chatbot/knowledge`
- PUT `/api/chatbot/knowledge/{entry_id}`
- DELETE `/api/chatbot/knowledge/{entry_id}`

Staff UI:

- `services/api_gateway/templates/staff_knowledge.html` goi cac endpoint nay.

Luu y: custom KB nay o Postgres va search keyword, khong co embedding/vector index rieng.

### 13.2. Request tu UI vao chatbot

Base template:

- `services/api_gateway/templates/base.html` co chatbot UI va goi `/api/chatbot/ask`.

Gateway:

- `services/api_gateway/gateway/middleware.py` lines 68-70 route `/api/chatbot/` sang `chatbot-service:8000`.

### 13.3. Chat request schema

Lines 73-78:

```python
class ChatRequest(BaseModel):
    user_id: int
    message: Optional[str] = ""
    trigger: Optional[str] = "chat"
    product_id: Optional[int] = None
```

### 13.4. Step 1: ghi action vao Neo4j

Trong `/api/chatbot/ask`, lines 228-234:

- Neu `trigger` nam trong `view`, `cart`, `search` va co `product_id`, goi `kb.record_user_action()`.
- `record_user_action()` trong `kb_client.py` lines 92-107:
  - `view` -> `VIEWED`
  - `cart` -> `ADDED_TO_CART`
  - `search` -> `SEARCHED`
  - MERGE relationship tu User toi Product.

Day la mot trong it noi runtime ghi truc tiep vao Neo4j sau khi import.

### 13.5. Step 2: semantic search product bang Qdrant

`qdrant_semantic_search()` lines 173-183:

- Goi `http://recommendation-search-service:8002/api/recommendations/search`.
- Query la message user.
- Return `recommendations` tu Qdrant.

Trong ask endpoint:

- Lines 236-241: neu co message, lay `qdrant_products`.

### 13.6. Step 3: search policy/FAQ trong custom KB

`search_custom_kb()` lines 185-215:

- Doc all rows trong `knowledge_bases`.
- Tach query thanh word.
- Score bang so word xuat hien trong `title + content`.
- Return top 3.

Trong ask:

- Lines 243-248 tao `kb_context` tu ket qua.

Day la "RAG context" cho policy/FAQ, nhung la keyword retrieval trong Postgres, khong phai vector RAG.

### 13.7. Step 4: lay history tu Neo4j

Lines 250-255:

- Goi `kb.get_user_history(req.user_id)`.
- Query trong `kb_client.py` lines 20-33.
- Lay toi da 10 action gan nhat gom VIEW/CART/SEARCH toi Product.

### 13.8. Step 5: tao candidate product

Lines 257-279:

- `candidate_ids` ban dau rong.
- Them product id tu `qdrant_products`.
- Them product id tu `kb.get_top_rated_products(10)`.

`get_top_rated_products()` doc Neo4j Product order by rating, nhung rating co the khong duoc set.

### 13.9. Step 6: GRU rank candidates

`chatbot_app/ai_engine.py`:

- Lines 18-25 khoi tao AIEngine.
- Lines 27-40 load `/app/AI/new/GRU_best_model.h5` va `/app/AI/new/encoders.pkl`.
- Lines 70-124 `predict_purchase_probability()`.

Trong chatbot ask:

- Lines 281-285 tao `excluded_ids` va `chronological_history`.
- Lines 289-313:
  - Lay product details tu Neo4j.
  - Với tung candidate, goi GRU probability.
  - Sort probability giam dan.
  - Lay top 3 lam `suggested_products`.

Neu AI khong ready hoac fail:

- Lines 315-319 fallback top products tu Neo4j.

### 13.10. Step 7: vouchers tu Neo4j

Lines 321-326:

- `kb.get_active_vouchers(5)`.
- Query Voucher active trong Neo4j.

### 13.11. Step 8: tao prompt context

Lines 328-336 tao `context_data`:

- `history`: danh sach `"ACTION product_name"`.
- `top_products`: ten top products.
- `ai_prediction`: ten product top.
- `ai_suggestions`: ten suggested products.
- `vouchers`: voucher code/discount.
- `kb_context`: policy/FAQ tu Postgres custom KB.

### 13.12. Step 9: goi LLM hoac fallback local

`freellm_client.py`:

- Lines 5: Gemini endpoint `gemini-2.5-flash:generateContent`.
- Lines 8-18: lay `GEMINI_API_KEY`; neu khong co thi return None.
- Lines 20-36: tao prompt tieng Viet voi history, suggestion, voucher, kb_context.
- Lines 38-60: POST toi Gemini.

Trong chatbot ask:

- Lines 338-343: thu `llm.chat_with_context()`.
- Lines 345-346: neu LLM khong tra response thi `brain.synthesize()`.
- Lines 350-357 return:
  - `reply`
  - `recommendations`
  - `engine: "Dynamic RAG"`
  - `prediction`
  - debug

## 14. Knowledge service FastAPI rieng

File: `services/knowledge_service/main.py`.

No tao FastAPI `Knowledge Base Service` voi:

- `/recommendations/{user_id}`:

```cypher
MATCH (u:User {id: $uid})-[:BOUGHT]->(p:Product)<-[:BOUGHT]-(other:User)-[:BOUGHT]->(reco:Product)
WHERE NOT (u)-[:BOUGHT]->(reco) AND reco <> p
RETURN reco.id as id, count(*) as weight
ORDER BY weight DESC LIMIT 5
```

- `/path/{user_id}/{product_id}` dung `shortestPath`.

Nhung gateway middleware khong route `/api/knowledge` hay `/recommendations` sang service nay. Trong luong UI hien tai, Neo4j chu yeu duoc dung qua:

- `recommendation_service.GraphClient`.
- `chatbot_service.chatbot_app.kb_client.KBClient`.

## 15. Phan AI model GRU

Co hai runtime load cung asset:

1. Recommendation service:
   - `services/recommendation_service/main.py`
   - `PurchaseModel` lines 255-327.
   - Model path env-driven, default `/app/AI/new/GRU_best_model.h5`.

2. Chatbot service:
   - `services/chatbot_service/chatbot_app/ai_engine.py`
   - `AIEngine` lines 18-132.
   - Hard-code `/app/AI/new/GRU_best_model.h5` va `/app/AI/new/encoders.pkl`.

Input logic giong nhau:

```text
history 20 event gan nhat
  -> behavior_encoder
  -> item_encoder
  -> category_encoder
target product
  -> item_encoder
  -> model.predict(...)
  -> probability/score
```

Behavior normalization:

- Recommendation service da tao behavior san: `pv`, `cart`, `buy`.
- Chatbot AIEngine normalize:
  - view/pv -> `pv`
  - cart/add_to_cart -> `cart`
  - purchase/buy/bought -> `buy`

## 16. UI nhan ket qua AI nhu the nao

Homepage:

- File `services/api_gateway/templates/homepage.html`.
- Lines 220-248 load `/api/recommendations/{userId}`.
- Lines 250-296 render card.
- Neu `r.source === 'qdrant_context'`, badge hien `Semantic`.
- Neu co score, hien `% Buy`.

Cart:

- File `services/api_gateway/templates/cart.html`.
- Lines 456-489 load recommendation.
- Lines 491-520+ render card.
- Cung phan biet `qdrant_context`.

Search page:

- File `services/api_gateway/templates/search.html`.
- Lines 25-44 goi `/api/recommendations/search?query=...`.
- Neu semantic search fail/rong thi fallback `/api/products/?search=...`.

Staff Knowledge:

- File `services/api_gateway/templates/staff_knowledge.html`.
- Quan ly CRUD `/api/chatbot/knowledge`.
- Data vao `chatbot_db.knowledge_bases`, khong vao Neo4j/Qdrant.

## 17. Nhung diem de nham/luu y quan trong

1. **Qdrant insert khong doc CSV truc tiep**
   - Qdrant lay products qua `product-service`.
   - Product-service lay tu `product_db`, ma `product_db` duoc seed tu CSV.

2. **Neo4j import hien tai khong dung `data_user500.csv`**
   - `importer.import_data("/data_user500.csv")` bi comment.
   - Neo4j import users/products/vouchers/tracking tu PostgreSQL.

3. **Chatbot custom knowledge base khong nam trong Neo4j**
   - Table `knowledge_bases` nam trong `chatbot_db`.
   - Search bang keyword count, khong embedding.

4. **Search semantic that su nam o `recommendation-search-service`**
   - File `search_server.py` encode query roi search Qdrant.
   - Gateway route `/api/recommendations/search` sang service nay.

5. **Recommendation service cung co `/api/recommendations/search`, nhung route UI khong uu tien no**
   - Trong recommendation service, search Qdrant la scroll + keyword scoring payload, khong vector query.

6. **Neo4j recommendation candidate phu thuoc `ADDED_TO_CART` seed**
   - `_related_products()` tim other users co `ADDED_TO_CART` voi seed product.
   - Neu graph thieu relation `ADDED_TO_CART`, candidate co the it va fallback popular.

7. **`get_top_rated_products()` co the khong that su top rated**
   - Importer khong set `p.rating`.
   - Query order by `COALESCE(p.rating, 0.0)`.

8. **`BOUGHT` khong nam trong chatbot `get_user_history()`**
   - Chatbot history query chi lay VIEW/CART/SEARCH toi Product.
   - Recommendation service lay purchase history tu order/tracking API rieng, khong phu thuoc chatbot history.

9. **Neo4j auth tat nhung code van truyen password**
   - Docker compose set `NEO4J_AUTH=none` va disable auth.
   - Code truyen `neo4j/password123`; trong config hien tai van chay vi auth disabled.

10. **GRU model la optional fallback-friendly**
    - Neu TensorFlow/model/encoder fail, recommendation service van chay bang graph score/popular.
    - Chatbot fallback sang top products/local brain.

## 18. Flow tong hop bang chu

### 18.1. Setup data

```text
AI/data/*.csv
  -> knowledge_service/db_seeder.py
  -> auth_db/product_db/tracking_db
  -> knowledge_service/sync_operational_db.py
  -> cart_db/order_db

voucher_service/seed_vouchers.py
  -> voucher_db

user_service/seed_users.py + seed_roles.py
  -> auth_db
```

### 18.2. Build Qdrant

```text
product_db
  -> product-service /api/products/
  -> vector_service/main.py fetch_products()
  -> format_product_text()
  -> SentenceTransformer all-MiniLM-L6-v2
  -> vector 384 dimensions
  -> Qdrant collection products, cosine
```

### 18.3. Build Neo4j

```text
auth_db.user
product_db.categories/products
voucher_db.vouchers
tracking_db.product_views/cart_actions/purchase_actions/search_history
  -> knowledge_service/importer.py
  -> Neo4j:
     User, Product, Category, Voucher, Search
     Product-BELONGS_TO->Category
     User-VIEWED/ADDED_TO_CART/CART_ACTION/BOUGHT->Product
     User-SEARCHED->Search
```

### 18.4. User search

```text
Browser search page
  -> API Gateway /api/recommendations/search
  -> recommendation-search-service
  -> encode query
  -> Qdrant vector search
  -> product-service enrich
  -> render products
```

### 18.5. Personalized recommendation

```text
Homepage/cart
  -> API Gateway /api/recommendations/{user_id}
  -> recommendation-service
  -> get cart from cart-service
  -> get purchase from order-service
  -> get tracking history from tracking-service
  -> Neo4j graph candidates
  -> Qdrant semantic context candidates
  -> GRU model score candidates
  -> return qdrant_context first + scored graph/GRU products
```

### 18.6. Chatbot

```text
Chat UI
  -> API Gateway /api/chatbot/ask
  -> chatbot-service
  -> optionally write user action to Neo4j
  -> Qdrant semantic product search by message
  -> Postgres chatbot_db keyword KB search
  -> Neo4j user history/top products/vouchers
  -> GRU rank candidate products
  -> Gemini response if key exists
  -> LocalBrain fallback if no Gemini
  -> reply + product recommendations
```

## 19. File index nhanh

- `docker-compose.yml`: khai bao Qdrant, Neo4j, recommendation, knowledge, chatbot, vector/search services.
- `quick_start.sh`: thu tu setup full AI.
- `fast_reload.sh`: rebuild AI service va vector index nhanh.
- `quick_update.sh`: update services, seed lai data, refresh Neo4j.
- `services/knowledge_service/db_seeder.py`: CSV -> PostgreSQL.
- `services/knowledge_service/sync_operational_db.py`: tracking -> cart/order operational DB.
- `services/knowledge_service/importer.py`: PostgreSQL -> Neo4j.
- `services/knowledge_service/main.py`: Neo4j API nho, it/khong duoc gateway dung.
- `services/vector_service/main.py`: product-service -> embedding -> Qdrant upsert.
- `services/vector_service/search_server.py`: query -> embedding -> Qdrant semantic search.
- `services/recommendation_service/main.py`: personalized recommendation pipeline.
- `services/chatbot_service/main.py`: chatbot FastAPI runtime hien tai.
- `services/chatbot_service/chatbot_app/kb_client.py`: Neo4j helper cho chatbot.
- `services/chatbot_service/chatbot_app/ai_engine.py`: GRU helper cho chatbot.
- `services/chatbot_service/chatbot_app/freellm_client.py`: Gemini client.
- `services/api_gateway/gateway/middleware.py`: route API sang microservices.
- `services/api_gateway/templates/homepage.html`: homepage recommendation UI.
- `services/api_gateway/templates/cart.html`: cart recommendation UI.
- `services/api_gateway/templates/search.html`: semantic search UI.
- `services/api_gateway/templates/staff_knowledge.html`: custom KB CRUD UI.

