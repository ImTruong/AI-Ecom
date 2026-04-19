from fastapi import FastAPI, HTTPException
import requests
import numpy as np
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Recommendation Service")

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class ChatRequest(BaseModel):
    message: str

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

async def calculate_user_embedding(user_id: int):
    """Calculate the weighted average embedding for a user based on their history"""
    # 1. Fetch user history from tracking service
    try:
        url = f"{TRACKING_SERVICE_URL}user-history/{user_id}/"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        history_data = resp.json()
        history = history_data.get('data', {})
    except Exception as e:
        print(f"❌ Tracking Service Error: {e}")
        return None, []

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

    if not actions:
        return None, []

    # 2. Fetch vectors for these products from Qdrant
    product_ids = list(set(a['product_id'] for a in actions))
    
    try:
        points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=product_ids,
            with_vectors=True
        )
    except Exception:
        return None, []

    if not points:
        return None, []

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
        return None, []

    return (averaged_vector / total_weight).tolist(), actions

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
    
    averaged_vector, actions = await calculate_user_embedding(user_id)

    if not averaged_vector:
        return await get_fallback_products(limit)

    product_ids = list(set(a['product_id'] for a in actions))

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

@app.post("/api/ai-chat/{user_id}")
async def ai_chat(user_id: int, chat_req: ChatRequest):
    """AI Assistant: Uses User Embedding + Gemini to answer questions with product context"""
    ensure_collection()
    
    # 1. Get User's Behavioral Profile (Embedding)
    user_vector, _ = await calculate_user_embedding(user_id)
    
    context_products = []
    if user_vector:
        # Search for products relevant to user's general taste
        try:
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=user_vector,
                limit=5
            )
            for r in results:
                name = r.payload.get('name', 'Unknown Product')
                cat = r.payload.get('category', 'General')
                context_products.append(f"- {name} ({cat})")
        except Exception as e:
            print(f"❌ Qdrant Search Error in Chat: {e}")

    # 2. Build Prompt
    context_str = "\n".join(context_products) if context_products else "No specific preference history found."
    
    prompt = f"""
    You are a helpful e-commerce AI assistant. 
    The user is asking: "{chat_req.message}"
    
    User Profile Context (Products they seem to like based on behavior):
    {context_str}
    
    Please answer the user's question. If you recommend something, base it on their profile context if relevant. 
    Be concise, friendly, and helpful.
    """

    # 3. Call LLM
    if not GEMINI_API_KEY:
        return {
            "success": True,
            "answer": f"I see you're interested in: {', '.join([p.split('(')[0].strip('- ') for p in context_products]) if context_products else 'our store'}. (Note: Gemini API key not configured, returning mock response for: {chat_req.message})",
            "context_count": len(context_products)
        }

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return {
            "success": True,
            "answer": response.text,
            "context_count": len(context_products)
        }
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")

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
