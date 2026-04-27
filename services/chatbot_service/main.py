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
    from chatbot_app.freellm_client import get_freellm_client
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
        llm = get_freellm_client()

        # 1. RECORD REAL ACTION
        if req.trigger in ['view', 'cart', 'search'] and req.product_id:
            try:
                action_map = {'view': 'VIEW', 'cart': 'CART', 'search': 'SEARCH'}
                kb.record_user_action(req.user_id, action_map.get(req.trigger, 'VIEW'), req.product_id)
            except Exception as e:
                print(f"[KB] Record action failed: {e}")

        # 2. RETRIEVE DYNAMIC CONTEXT
        history = []
        try:
            history = kb.get_user_history(req.user_id)
        except Exception as e:
            print(f"[KB] History fetch failed: {e}")

        # AI Prediction from LSTM
        prediction = "Không có"
        predicted_products = []
        try:
            actions = [h['action'] for h in history if h.get('action')]
            product_ids = [h['product_id'] for h in history if h.get('product_id')]
            if actions and product_ids:
                pred = ai.predict_next_product(actions, product_ids)
                if pred and pred.get("top_3"):
                    pred_details = kb.get_product_details(pred["top_3"])
                    if pred_details:
                        predicted_products = pred_details
                        prediction = pred_details[0].get('name', prediction)
        except Exception as e:
            print(f"[AI] Prediction failed: {e}")

        top_products_data = []
        try:
            top_products_data = kb.get_top_rated_products(10) # Fetch more for variety
        except Exception as e:
            print(f"[KB] Top products fetch failed: {e}")
        
        # 3. Dynamic Recommendations
        suggested_products = []
        if predicted_products:
            suggested_products = predicted_products
        elif top_products_data:
            # Use top 3 recommendations dynamically
            top_ids = [p['id'] for p in top_products_data[:3]]
            suggested_products = kb.get_product_details(top_ids)

        vouchers = []
        try:
            vouchers = kb.get_active_vouchers(5)
        except Exception as e:
            print(f"[KB] Voucher fetch failed: {e}")

        context_data = {
            "history": [f"{h['action']} {h['name']}" for h in history],
            "top_products": [p['name'] for p in top_products_data],
            "ai_prediction": prediction,
            "ai_suggestions": [p.get('name') for p in predicted_products],
            "vouchers": [f"{v['code']} ({v['discount_value']})" for v in vouchers]
        }

        # 4. GENERATE DYNAMIC RESPONSE
        response_text = None
        try:
            response_text = llm.chat_with_context(req.message or "", context_data, req.trigger)
        except Exception as e:
            print(f"[FREELLM] Request failed: {e}")

        if not response_text:
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
            "recommendations": [],
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
