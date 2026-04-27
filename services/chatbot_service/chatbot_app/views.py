from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_engine import get_ai_engine
from .kb_client import get_kb_client
from .local_brain import get_local_brain
from .freellm_client import get_freellm_client
import random
import re
import logging

logger = logging.getLogger(__name__)

# Keywords that indicate user wants to search/buy a product
BUY_KEYWORDS = [
    'mua', 'tim', 'co', 'ban', 'gia', 'muon', 'muốn', 'tìm', 'tìm kiếm', 
    'mua sắm', 'muasam', 'mua sam', 'cần', 'can', 'mua ngay', 'đặt', 'dat',
    'giá', 'bao nhiêu', 'bn', 'giá bao nhiêu', 'cheap', 'rẻ', 're'
]

# Product category keywords
PRODUCT_KEYWORDS = [
    'iphone', 'samsung', 'macbook', 'laptop', 'ao', 'quan', 'giay', 
    'áo', 'quần', 'giày', 'dien thoai', 'điện thoại', 'dt', 'tivi', 'tv',
    'ipad', 'tablet', 'máy tính', 'may tinh', 'pc', 'desktop', 'phụ kiện', 'phu kien'
]

def is_buying_intent(message):
    """Check if user message indicates intent to buy/search for a product"""
    if not message:
        logger.debug("[CHATBOT] Empty message, no buying intent")
        return False
    msg_lower = message.lower().strip()
    
    # Check for product names or buying keywords
    has_product_name = any(term in msg_lower for term in PRODUCT_KEYWORDS)
    has_buy_keyword = any(kw in msg_lower for kw in BUY_KEYWORDS)
    
    logger.info(f"[CHATBOT] Checking buying intent for: '{msg_lower}'")
    logger.info(f"[CHATBOT] has_product_name: {has_product_name}, has_buy_keyword: {has_buy_keyword}")
    
    return has_product_name or has_buy_keyword

class ChatbotAIView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        message = request.data.get('message', '')
        trigger = request.data.get('trigger') # 'search', 'cart', 'chat'

        logger.info(f"[CHATBOT] Request received - user_id: {user_id}, trigger: {trigger}, message: '{message}'")

        if not user_id:
            logger.error("[CHATBOT] User ID missing")
            return Response({"success": False, "error": "User ID required"}, status=400)

        kb = get_kb_client()
        ai = get_ai_engine()
        brain = get_local_brain()
        llm = get_freellm_client()

        logger.info(f"[CHATBOT] KB: {kb is not None}, AI: {ai is not None}, LLM: {llm is not None}")

        # 1. Fetch user history from KB (Neo4j)
        history = kb.get_user_history(user_id)
        actions = [h['action'] for h in history]
        pids = [h['product_id'] for h in history]
        logger.info(f"[CHATBOT] User history: {len(history)} actions")

        # 2. Get AI recommendation
        ai_recommendation = None
        if ai and actions:
            ai_recommendation = ai.predict_next_product(actions, pids)
            logger.info(f"[CHATBOT] AI recommendation: {ai_recommendation}")

        # 3. Formulate Response using RAG
        response_text = None
        suggested_products = []
        prediction_name = "Khong co"
        predicted_products = []
        
        # Handle explicit buying/search intent FIRST - before any AI recommendations
        buying_intent = is_buying_intent(message)
        logger.info(f"[CHATBOT] Buying intent detected: {buying_intent}")
        
        if buying_intent:
            logger.info(f"[CHATBOT] Searching KB for: '{message}'")
            search_results = kb.search_products(message, limit=5)
            logger.info(f"[CHATBOT] KB search returned {len(search_results)} results")
            
            if search_results:
                top = search_results[0]
                response_text = f"Tôi đã tìm thấy sản phẩm phù hợp: {top.get('name')} (giá: {top.get('price', 0):,.0f}đ). Bạn có thể xem chi tiết tại /product/detail/{top.get('id')}/"
                suggested_products = [
                    {
                        'id': r.get('id'),
                        'name': r.get('name'),
                        'price': r.get('price'),
                        'category': r.get('category', ''),
                        'image_url': r.get('image_url', '')
                    }
                    for r in search_results
                ]
                logger.info(f"[CHATBOT] Returning product search results")
            else:
                # No exact match - suggest similar products from top rated
                logger.info(f"[CHATBOT] No exact match, getting top rated products")
                similar = kb.get_top_rated_products(5)
                if similar:
                    response_text = "Tôi chưa tìm thấy sản phẩm đó trong hệ thống. Đây là các sản phẩm tương tự bạn có thể quan tâm."
                    suggested_products = similar
        
        # If no buying intent or no search results, use AI recommendation
        if not response_text and ai_recommendation:
            top_ids = ai_recommendation['top_3']
            details = kb.get_product_details(top_ids)
            suggested_products = details
            
            main_prod = details[0] if details else None
            if main_prod:
                prediction_name = main_prod.get('name', prediction_name)
            predicted_products = details
            
            if main_prod:
                if trigger == 'cart':
                    response_text = f"Toi thay ban vua them hang vao gio. Dua tren so thich cua ban, co the ban se thich '{main_prod['name']}' ({main_prod['category']}) day!"
                elif trigger == 'search':
                    response_text = f"Ket qua tim kiem day! Ngoai ra, he thong AI cua toi goi y ban nen xem qua '{main_prod['name']}' vi no rat hop voi phong cach cua ban."
                else:
                    response_text = f"Chao ban! Toi da phan tich lich su mua sam cua ban. Ban co muon xem thu '{main_prod['name']}' khong? No dang rat hot trong danh muc {main_prod['category']}."

        top_products = kb.get_top_rated_products(5)
        vouchers = kb.get_active_vouchers(3)

        # Build context for LLM - but DON'T include raw history
        # Only include summary stats and AI predictions
        context_data = {
            "history_count": len(history),
            "top_products": [p['name'] for p in top_products],
            "ai_prediction": prediction_name,
            "ai_suggestions": [p.get('name') for p in predicted_products],
            "vouchers": [f"{v['code']} ({v['discount_value']})" for v in vouchers],
        }

        # Only use LLM if no direct response yet
        if not response_text:
            response_text = llm.chat_with_context(message, context_data, trigger)

        if not response_text:
            if ai_recommendation:
                response_text = "Chào bạn! Tôi có vài gợi ý dựa trên lịch sử mua sắm của bạn."
            else:
                response_text = "Chào bạn! Tôi là trợ lý AI. Bạn cần tìm kiếm sản phẩm gì hôm nay?"

        logger.info(f"[CHATBOT] Final response: '{response_text[:100]}...' with {len(suggested_products)} suggestions")

        return Response({
            "success": True,
            "reply": response_text,
            "recommendations": suggested_products,
            "actions_analyzed": len(actions),
            "debug": {
                "buying_intent": buying_intent,
                "trigger": trigger,
                "history_count": len(history)
            }
        })

class ChatbotStatusView(APIView):
    def get(self, request):
        ai = get_ai_engine()
        return Response({
            "status": "online",
            "ai_loaded": ai is not None,
            "kb_connected": True
        })
