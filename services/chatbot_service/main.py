from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
import traceback

try:
    from chatbot_app.ai_engine import get_ai_engine
    from chatbot_app.kb_client import get_kb_client
    from chatbot_app.local_brain import get_local_brain
except Exception as e:
    print(f"Startup Import Error: {e}")

app = FastAPI(title="AI Chatbot RAG Service (Dynamic)")

class ChatRequest(BaseModel):
    user_id: int
    message: Optional[str] = ""
    trigger: Optional[str] = "chat" 
    product_id: Optional[int] = None

@app.post("/api/chatbot/ask")
async def ask_chatbot(req: ChatRequest):
    try:
        kb = get_kb_client()
        brain = get_local_brain()
        ai = get_ai_engine()

        # 1. RECORD REAL ACTION
        if req.trigger in ['view', 'cart', 'search'] and req.product_id:
            try:
                action_map = {'view': 'VIEW', 'cart': 'CART', 'search': 'SEARCH'}
                kb.record_user_action(req.user_id, action_map.get(req.trigger, 'VIEW'), req.product_id)
            except: pass

        # 2. RETRIEVE DYNAMIC CONTEXT
        history = []
        try:
            history = kb.get_user_history(req.user_id)
        except: pass

        # AI Prediction from LSTM
        prediction = "Không có"
        try:
            prediction = ai.predict_next_action(req.user_id)
        except: pass

        top_products_data = []
        try:
            top_products_data = kb.get_top_rated_products(10) # Fetch more for variety
        except: pass
        
        # 3. Dynamic Recommendations
        suggested_products = []
        if top_products_data:
            # Use top 3 recommendations dynamically
            top_ids = [p['id'] for p in top_products_data[:3]]
            suggested_products = kb.get_product_details(top_ids)

        context_data = {
            "history": [f"{h['action']} {h['name']}" for h in history],
            "top_products": [p['name'] for p in top_products_data],
            "ai_prediction": prediction
        }

        # 4. GENERATE DYNAMIC RESPONSE
        response_text = brain.synthesize(req.message or "", context_data, req.trigger)

        return {
            "success": True,
            "reply": response_text,
            "recommendations": suggested_products,
            "engine": "Dynamic RAG",
            "prediction": prediction
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": True,
            "reply": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
            "recommendations": []
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
