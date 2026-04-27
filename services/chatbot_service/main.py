from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
import traceback
import logging

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

# Keywords that indicate user wants to search/buy a product
BUY_KEYWORDS = [
    'mua', 'tim', 'co', 'ban', 'gia', 'muon', 'muốn', 'tìm', 'tìm kiếm', 
    'mua sắm', 'muasam', 'mua sam', 'cần', 'can', 'mua ngay', 'đặt', 'dat',
    'giá', 'bao nhiêu', 'bn', 'giá bao nhiêu', 'cheap', 'rẻ', 're'
]

PRODUCT_KEYWORDS = [
    'iphone', 'samsung', 'macbook', 'laptop', 'ao', 'quan', 'giay', 
    'áo', 'quần', 'giày', 'dien thoai', 'điện thoại', 'dt', 'tivi', 'tv',
    'ipad', 'tablet', 'máy tính', 'may tinh', 'pc', 'desktop', 'phụ kiện', 'phu kien',
    'sạc', 'sac', 'tai nghe', 'tainghe', 'chuột', 'chuot', 'bàn phím', 'ban phim'
]

def is_buying_intent(message):
    """Check if user message indicates intent to buy/search for a product"""
    if not message:
        return False
    msg_lower = message.lower().strip()
    has_product = any(term in msg_lower for term in PRODUCT_KEYWORDS)
    has_buy_kw = any(kw in msg_lower for kw in BUY_KEYWORDS)
    return has_product or has_buy_kw

class ChatRequest(BaseModel):
    user_id: int
    message: Optional[str] = ""
    trigger: Optional[str] = "chat" 
    product_id: Optional[int] = None

@app.post("/api/chatbot/ask")
async def ask_chatbot(req: ChatRequest):
    logger.info(f"[CHATBOT] Request: user_id={req.user_id}, trigger={req.trigger}, message='{req.message}'")
    
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
                logger.error(f"[KB] Record action failed: {e}")

        # CHECK BUYING INTENT FIRST
        buying_intent = is_buying_intent(req.message)
        logger.info(f"[CHATBOT] Buying intent: {buying_intent}")
        
        if buying_intent and req.message:
            logger.info(f"[CHATBOT] Searching KB for: '{req.message}'")
            try:
                search_results = kb.search_products(req.message, limit=5)
                logger.info(f"[CHATBOT] Found {len(search_results)} results")
                
                if search_results:
                    top = search_results[0]
                    response_text = f"Tôi đã tìm thấy sản phẩm phù hợp: {top.get('name')} (giá: {top.get('price', 0):,.0f}đ). Bạn có thể xem chi tiết tại /product/detail/{top.get('id')}/"
                    
                    return {
                        "success": True,
                        "reply": response_text,
                        "recommendations": [
                            {
                                'id': r.get('id'),
                                'name': r.get('name'),
                                'price': r.get('price'),
                                'category': r.get('category', ''),
                                'image_url': r.get('image_url', '')
                            }
                            for r in search_results
                        ],
                        "engine": "KB Search",
                        "debug": {"buying_intent": True, "search_term": req.message}
                    }
                else:
                    # No results - suggest top rated
                    similar = kb.get_top_rated_products(5)
                    return {
                        "success": True,
                        "reply": "Tôi chưa tìm thấy sản phẩm đó. Đây là các sản phẩm phổ biến:",
                        "recommendations": similar,
                        "engine": "KB Fallback",
                        "debug": {"buying_intent": True, "no_results": True}
                    }
            except Exception as e:
                logger.error(f"[CHATBOT] Search error: {e}")

        # 2. RETRIEVE DYNAMIC CONTEXT
        history = []
        try:
            history = kb.get_user_history(req.user_id)
        except Exception as e:
            logger.error(f"[KB] History fetch failed: {e}")

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
            logger.error(f"[AI] Prediction failed: {e}")

        top_products_data = []
        try:
            top_products_data = kb.get_top_rated_products(10)
        except Exception as e:
            logger.error(f"[KB] Top products fetch failed: {e}")
        
        # 3. Dynamic Recommendations
        suggested_products = []
        if predicted_products:
            suggested_products = predicted_products
        elif top_products_data:
            top_ids = [p['id'] for p in top_products_data[:3]]
            suggested_products = kb.get_product_details(top_ids)

        vouchers = []
        try:
            vouchers = kb.get_active_vouchers(5)
        except Exception as e:
            logger.error(f"[KB] Voucher fetch failed: {e}")

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
            logger.error(f"[FREELLM] Request failed: {e}")

        if not response_text:
            response_text = brain.synthesize(req.message or "", context_data, req.trigger)

        logger.info(f"[CHATBOT] Response generated, {len(suggested_products)} suggestions")
        
        return {
            "success": True,
            "reply": response_text,
            "recommendations": suggested_products,
            "engine": "Dynamic RAG",
            "prediction": prediction,
            "debug": {"buying_intent": buying_intent, "history_count": len(history)}
        }

    except Exception as e:
        logger.exception("[CHATBOT] Fatal error")
        return {
            "success": True,
            "reply": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
            "recommendations": [],
            "error": str(e),
            "debug": {"error": str(e)}
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
