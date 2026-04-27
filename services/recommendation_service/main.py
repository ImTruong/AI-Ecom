from fastapi import FastAPI, HTTPException
import os
import requests
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Recommendation Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
TRACKING_SERVICE_URL = os.getenv('TRACKING_SERVICE_URL', 'http://tracking-service:8000/api/tracking/')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products/')
QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
COLLECTION_NAME = "products"
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')


client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

ACTION_WEIGHTS = {
    'view': 1,
    'cart': 2,
    'purchase': 3,
}

def ensure_collection():
    try:
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            print(f"⚠️ Collection '{COLLECTION_NAME}' does not exist. Creating empty collection...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )
    except Exception as e:
        print(f"❌ Error checking/creating collection: {e}")

def qdrant_search(query_vector, limit):
    if hasattr(client, "search"):
        return client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
    if hasattr(client, "search_points"):
        return client.search_points(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
    search_request = models.SearchRequest(
        vector=query_vector,
        limit=limit,
        with_payload=True,
        with_vector=False
    )
    response = client.http.search_api.search_points(
        collection_name=COLLECTION_NAME,
        search_request=search_request
    )
    return response.result

def payload_to_text(payload):
    if not payload:
        return ""
    raw_text = payload.get("raw_text")
    if raw_text:
        return raw_text
    parts = [
        f"Product Name: {payload.get('name', '')}",
        f"Category: {payload.get('category', '')}",
        f"Type: {payload.get('product_type', '')}",
    ]
    return ". ".join([p for p in parts if p]) + "."

def fetch_products(limit=6, search=None):
    try:
        params = {'search': search} if search else None
        resp = requests.get(PRODUCT_SERVICE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data[:limit]
    except Exception as e:
        print(f"❌ Product Service Error: {e}")
    return []

def build_recommendations_from_products(products, note=None):
    return {
        "success": True,
        "note": note,
        "recommendations": [{"id": p.get("id"), "payload": p} for p in products]
    }

def build_context_text(history, payload_map):
    lines = []
    for v in history.get('views', []):
        pid = int(v.get('product_id'))
        text = payload_to_text(payload_map.get(pid, {})) or f"Product ID {pid}"
        lines.extend([f"Viewed: {text}"] * ACTION_WEIGHTS['view'])

    for c in history.get('carts', []):
        pid = int(c.get('product_id'))
        text = payload_to_text(payload_map.get(pid, {})) or f"Product ID {pid}"
        lines.extend([f"Added to cart: {text}"] * ACTION_WEIGHTS['cart'])

    for p in history.get('purchases', []):
        pid = int(p.get('product_id'))
        text = payload_to_text(payload_map.get(pid, {})) or f"Product ID {pid}"
        lines.extend([f"Purchased: {text}"] * ACTION_WEIGHTS['purchase'])

    for s in history.get('searches', []):
        query = s.get('query')
        if query:
            lines.append(f"Search: {query}")

    return " ".join(lines).strip()

@app.get("/api/recommendations/search")
async def search_products(query: str, limit: int = 12):
    ensure_collection()

    if not query:
        return await get_fallback_products(limit)

    try:
        query_vector = embedding_model.encode(query).tolist()
        results = qdrant_search(query_vector, limit)
        recommendations = [{
            "id": r.id,
            "score": float(r.score),
            "payload": r.payload,
        } for r in results]
        if recommendations:
            return {
                "success": True,
                "query": query,
                "recommendations": recommendations
            }
    except Exception as e:
        print(f"❌ Qdrant Search Error: {e}")

    products = fetch_products(limit=limit, search=query)
    if products:
        return build_recommendations_from_products(products, note="Fallback to keyword search")

    return {"success": False, "error": "No results", "recommendations": []}

@app.get("/api/recommendations/{user_id}")
async def get_user_recommendations(user_id: int, limit: int = 6):
    ensure_collection()
    
    # 1. Fetch user history from tracking service
    try:
        url = f"{TRACKING_SERVICE_URL}user-history/{user_id}/"
        print(f"📡 Fetching history from: {url}")
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        history_data = resp.json()
        print(f"✅ History retrieved: {history_data.get('success')}")
        history = history_data.get('data', {})
    except Exception as e:
        print(f"❌ Tracking Service Error: {e}")
        # Try to return fallbacks instead of crashing
        return await get_fallback_products(limit)

    views = history.get('views', [])
    carts = history.get('carts', [])
    purchases = history.get('purchases', [])
    searches = history.get('searches', [])
    
    actions = []
    for v in views:
        actions.append(int(v['product_id']))
    for c in carts:
        actions.append(int(c['product_id']))
    for p in purchases:
        actions.append(int(p['product_id']))

    seen_ids = set(actions)

    print(f"📊 Total user actions: {len(actions)}")

    if not actions and not searches:
        return await get_fallback_products(limit)

    # 2. Fetch payloads for these products from Qdrant
    product_ids = list(set(actions))
    payload_map = {}
    if product_ids:
        try:
            points = client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=product_ids,
                with_payload=True,
                with_vectors=False
            )
            payload_map = {p.id: p.payload for p in points}
            print(f"💎 Retrieved {len(points)} payloads from Qdrant")
        except Exception as e:
            print(f"❌ Qdrant Retrieve Error: {e}")
            payload_map = {}

    # 3. Build user context and embed it
    context_text = build_context_text(history, payload_map)
    if not context_text:
        return await get_fallback_products(limit)

    query_vector = embedding_model.encode(context_text).tolist()

    # 4. Search Qdrant for similar products
    try:
        results = qdrant_search(query_vector, limit + len(product_ids))
    except Exception as e:
        print(f"❌ Qdrant Search Error: {e}")
        return await get_fallback_products(limit)

    # 5. Format results
    recommendations = []
    for r in results:
        if r.id in seen_ids:
            continue
        recommendations.append({
            "id": r.id,
            "score": float(r.score),
            "payload": r.payload,
            "is_previously_interacted": r.id in seen_ids
        })

    # Sort: Ensure the highest score is at position #1
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    if not recommendations:
        return await get_fallback_products(limit)

    return {
        "success": True,
        "user_id": user_id,
        "recommendations": recommendations[:limit],
        "history_count": len(actions) + len(searches)
    }

async def get_fallback_products(limit, search=None):
    try:
        ensure_collection()
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True
        )[0]
        if results:
            return {
                "success": True,
                "note": "Returning default products",
                "recommendations": [{"id": r.id, "payload": r.payload} for r in results]
            }
    except Exception as e:
        print(f"❌ Fallback Error: {e}")

    products = fetch_products(limit=limit, search=search)
    if products:
        return build_recommendations_from_products(products, note="Fallback to product service")

    return {"success": False, "error": "No fallback data", "recommendations": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
