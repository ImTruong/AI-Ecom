from fastapi import FastAPI, HTTPException
import requests
import numpy as np
import os
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
QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
COLLECTION_NAME = "products"

# Weights from user request
WEIGHTS = {
    'view': 1.0,
    'cart': 3.0,
    'purchase': 5.0
}

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

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

@app.get("/api/recommendations/{user_id}")
async def get_user_recommendations(user_id: int, limit: int = 10):
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
    
    actions = []
    for v in views:
        actions.append({'product_id': int(v['product_id']), 'weight': WEIGHTS['view']})
    for c in carts:
        actions.append({'product_id': int(c['product_id']), 'weight': WEIGHTS['cart']})
    for p in purchases:
        actions.append({'product_id': int(p['product_id']), 'weight': WEIGHTS['purchase']})

    print(f"📊 Total user actions: {len(actions)}")

    if not actions:
        return await get_fallback_products(limit)

    # 2. Fetch vectors for these products from Qdrant
    product_ids = list(set(a['product_id'] for a in actions))
    
    try:
        points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=product_ids,
            with_vectors=True
        )
        print(f"💎 Retrieved {len(points)} vectors from Qdrant")
    except Exception as e:
        print(f"❌ Qdrant Retrieve Error: {e}")
        return await get_fallback_products(limit)

    if not points:
        return await get_fallback_products(limit)

    # Map product_id to vector
    vector_map = {p.id: p.vector for p in points}

    # 3. Calculate Weighted Average Vector
    total_weight = 0
    averaged_vector = np.zeros(384) 
    
    for action in actions:
        pid = action['product_id']
        if pid in vector_map:
            weight = action['weight']
            vector = np.array(vector_map[pid])
            averaged_vector += vector * weight
            total_weight += weight

    if total_weight == 0:
        return await get_fallback_products(limit)

    averaged_vector = averaged_vector / total_weight

    # 4. Search Qdrant for similar products
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=averaged_vector.tolist(),
            limit=limit + len(product_ids)
        )
    except Exception as e:
        print(f"❌ Qdrant Search Error: {e}")
        return await get_fallback_products(limit)

    # 5. Filter and format
    seen_ids = set(product_ids)
    recommendations = []
    
    # First pass: try to find new products (not seen)
    for r in results:
        if r.id not in seen_ids:
            recommendations.append({
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            })
            if len(recommendations) >= limit:
                break
    
    # Second pass: if we don't have enough, allow seen products (if the catalog is small)
    if len(recommendations) < limit:
        for r in results:
            if r.id in seen_ids and not any(rec['id'] == r.id for rec in recommendations):
                recommendations.append({
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                    "note": "Already viewed"
                })
                if len(recommendations) >= limit:
                    break

    # Final Sort: Ensure the highest score is at position #1
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return {
        "success": True,
        "user_id": user_id,
        "recommendations": recommendations,
        "history_count": len(actions)
    }

async def get_fallback_products(limit):
    try:
        ensure_collection()
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True
        )[0]
        
        return {
            "success": True,
            "note": "Returning default products",
            "recommendations": [{"id": r.id, "payload": r.payload} for r in results]
        }
    except Exception as e:
        print(f"❌ Fallback Error: {e}")
        return {"success": False, "error": str(e), "recommendations": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
