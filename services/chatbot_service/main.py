from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
import traceback
import logging
import requests
import psycopg2
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from chatbot_app.ai_engine import get_ai_engine
    from chatbot_app.kb_client import get_kb_client
    from chatbot_app.local_brain import get_local_brain
    from chatbot_app.freellm_client import get_freellm_client
except Exception as e:
    logger.error(f"Startup Import Error: {e}")

app = FastAPI(title="AI Chatbot RAG Service (Dynamic)")

# Database configuration and connection helpers
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set in environment")
    url = urlparse(db_url)
    return psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432
    )

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("[DB] Table 'knowledge_bases' verified/created.")
    except Exception as e:
        logger.error(f"[DB] Database initialization error: {e}")

@app.on_event("startup")
def startup_event():
    init_db()

# Pydantic schemas for Knowledge Base CRUD
class KBEntryCreate(BaseModel):
    title: str
    content: str
    category: str

# Pydantic schemas for Chat
class ChatRequest(BaseModel):
    user_id: int
    message: Optional[str] = ""
    trigger: Optional[str] = "chat" 
    product_id: Optional[int] = None

# Custom Knowledge Base CRUD endpoints
@app.get("/api/chatbot/knowledge", response_model=List[dict])
def list_knowledge_entries():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content, category, created_at FROM knowledge_bases ORDER BY id DESC")
        rows = cursor.fetchall()
        results = [
            {
                "id": r[0],
                "title": r[1],
                "content": r[2],
                "category": r[3],
                "created_at": r[4].isoformat() if r[4] else ""
            }
            for r in rows
        ]
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"[KB-CRUD] Error fetching entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot/knowledge", status_code=201)
def create_knowledge_entry(entry: KBEntryCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_bases (title, content, category) VALUES (%s, %s, %s) RETURNING id, created_at",
            (entry.title, entry.content, entry.category)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "success": True,
            "id": row[0],
            "title": entry.title,
            "content": entry.content,
            "category": entry.category,
            "created_at": row[1].isoformat() if row[1] else ""
        }
    except Exception as e:
        logger.error(f"[KB-CRUD] Error creating entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/chatbot/knowledge/{entry_id}")
def update_knowledge_entry(entry_id: int, entry: KBEntryCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE knowledge_bases SET title = %s, content = %s, category = %s WHERE id = %s RETURNING id",
            (entry.title, entry.content, entry.category, entry_id)
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"success": True, "id": entry_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[KB-CRUD] Error updating entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chatbot/knowledge/{entry_id}")
def delete_knowledge_entry(entry_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_bases WHERE id = %s RETURNING id", (entry_id,))
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"success": True, "id": entry_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[KB-CRUD] Error deleting entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper search functions
def qdrant_semantic_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        url = "http://recommendation-search-service:8002/api/recommendations/search"
        response = requests.get(url, params={"query": query, "limit": limit}, timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("recommendations", [])
    except Exception as e:
        logger.error(f"[QDRANT] Search error: {e}")
    return []

def search_custom_kb(query: str) -> List[Dict[str, Any]]:
    if not query:
        return []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title, content, category FROM knowledge_bases")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        words = [w.strip() for w in query.lower().split() if w.strip()]
        if not words:
            return []
            
        matches = []
        for title, content, category in rows:
            text = f"{title} {content}".lower()
            match_score = sum(1 for w in words if w in text)
            if match_score > 0:
                matches.append({
                    "title": title,
                    "content": content,
                    "category": category,
                    "score": match_score
                })
        matches.sort(key=lambda m: m["score"], reverse=True)
        return matches[:3]
    except Exception as e:
        logger.error(f"[POSTGRES-KB] Search error: {e}")
        return []


@app.post("/api/chatbot/ask")
async def ask_chatbot(req: ChatRequest):
    logger.info(f"[CHATBOT] Request: user_id={req.user_id}, trigger={req.trigger}, message='{req.message}'")
    
    try:
        kb = get_kb_client()
        brain = get_local_brain()
        ai = get_ai_engine()
        llm = get_freellm_client()

        # 1. RECORD REAL ACTION IN NEO4J
        if req.trigger in ['view', 'cart', 'search'] and req.product_id:
            try:
                action_map = {'view': 'VIEW', 'cart': 'CART', 'search': 'SEARCH'}
                kb.record_user_action(req.user_id, action_map.get(req.trigger, 'VIEW'), req.product_id)
            except Exception as e:
                logger.error(f"[KB] Record action failed: {e}")

        # 2. SEMANTIC SEARCH & KB MATCHES
        # Qdrant vector search for products matching user queries
        qdrant_products = []
        if req.message:
            qdrant_products = qdrant_semantic_search(req.message, limit=5)
            logger.info(f"[CHATBOT] Qdrant found {len(qdrant_products)} matching products")

        # Custom FAQ/Policy searching in Postgres
        kb_matches = search_custom_kb(req.message or "")
        kb_context = "Không có"
        if kb_matches:
            kb_context = "\n".join([f"- {m['title']}: {m['content']}" for m in kb_matches])
            logger.info(f"[CHATBOT] Custom KB found {len(kb_matches)} matching policies")

        # 3. NEO4J USER HISTORY
        history = []
        try:
            history = kb.get_user_history(req.user_id)
        except Exception as e:
            logger.error(f"[KB] History fetch failed: {e}")

        # 4. GRU MODEL RANKING (MANDATORY PREDICT)
        # Fetch candidate product IDs from Qdrant and Neo4j popular/top products
        candidate_ids = []
        seen_candidates = set()
        
        # Add Qdrant semantic matches
        for item in qdrant_products:
            pid = item.get("id")
            if pid and pid not in seen_candidates:
                seen_candidates.add(pid)
                candidate_ids.append(pid)
                
        # Add Neo4j top rated/popular items to enrich candidates
        top_products_data = []
        try:
            top_products_data = kb.get_top_rated_products(10)
            for item in top_products_data:
                pid = item.get("id")
                if pid and pid not in seen_candidates:
                    seen_candidates.add(pid)
                    candidate_ids.append(pid)
        except Exception as e:
            logger.error(f"[KB] Top products fetch failed: {e}")

        # Exclude items user has already carted/bought in their history to avoid redundant suggestion
        excluded_ids = {int(h['product_id']) for h in history if h.get('action') in {'cart', 'buy', 'ADDED_TO_CART', 'BOUGHT'}}

        # Score candidates with GRU model using chronological user history (oldest first)
        chronological_history = history[::-1]
        suggested_products = []
        prediction = "Không có"

        if ai.ready and candidate_ids:
            try:
                candidate_details = kb.get_product_details(candidate_ids)
                products_info = {int(p['id']): p for p in candidate_details}
                
                scored_candidates = []
                for cid in candidate_ids:
                    if cid in excluded_ids or cid not in products_info:
                        continue
                    # Predict purchase probability using GRU model
                    prob = ai.predict_purchase_probability(chronological_history, cid, products_info)
                    if prob is not None:
                        scored_candidates.append((cid, prob))
                
                # Sort candidates by predicted purchase probability descending
                scored_candidates.sort(key=lambda x: x[1], reverse=True)
                top_ids = [cid for cid, prob in scored_candidates[:3]]
                
                # Retrieve full details for top ranked recommendations
                suggested_products = [products_info[cid] for cid in top_ids if cid in products_info]
                if suggested_products:
                    prediction = suggested_products[0].get('name', 'Không có')
                logger.info(f"[CHATBOT] Ranked {len(scored_candidates)} candidates. Top AI prediction: {prediction}")
            except Exception as e:
                logger.error(f"[AI] Candidate prediction ranking failed: {e}")

        # Fallback to top-rated if AI models failed or candidates empty
        if not suggested_products and top_products_data:
            suggested_products = top_products_data[:3]
            if suggested_products:
                prediction = suggested_products[0].get('name', 'Không có')

        # 5. RETRIEVE ACTIVE VOUCHERS
        vouchers = []
        try:
            vouchers = kb.get_active_vouchers(5)
        except Exception as e:
            logger.error(f"[KB] Voucher fetch failed: {e}")

        # 6. ASSEMBLE PROMPT CONTEXT
        context_data = {
            "history": [f"{h['action']} {h['name']}" for h in history],
            "top_products": [p['name'] for p in top_products_data],
            "ai_prediction": prediction,
            "ai_suggestions": [p.get('name') for p in suggested_products],
            "vouchers": [f"{v['code']} ({v['discount_value']})" for v in vouchers],
            "kb_context": kb_context
        }

        # 7. GENERATE DYNAMIC ANSWER
        response_text = None
        try:
            response_text = llm.chat_with_context(req.message or "", context_data, req.trigger)
        except Exception as e:
            logger.error(f"[FREELLM] LLM inference failed: {e}")

        if not response_text:
            response_text = brain.synthesize(req.message or "", context_data, req.trigger)

        logger.info(f"[CHATBOT] Response generated successfully. Recommending {len(suggested_products)} products.")
        
        return {
            "success": True,
            "reply": response_text,
            "recommendations": suggested_products,
            "engine": "Dynamic RAG",
            "prediction": prediction,
            "debug": {"buying_intent": bool(qdrant_products), "history_count": len(history)}
        }

    except Exception as e:
        logger.exception("[CHATBOT] Fatal execution error")
        return {
            "success": True,
            "reply": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
            "recommendations": [],
            "error": str(e),
            "debug": {"error": str(e)}
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
