from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_engine import get_ai_engine
from .kb_client import get_kb_client
import random

class ChatbotAIView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        message = request.data.get('message', '').lower()
        trigger = request.data.get('trigger') # 'search', 'cart', 'chat'

        if not user_id:
            return Response({"success": False, "error": "User ID required"}, status=400)

        kb = get_kb_client()
        ai = get_ai_engine()

        # 1. Fetch user history from KB (Neo4j)
        history = kb.get_user_history(user_id)
        actions = [h['action'] for h in history]
        pids = [h['product_id'] for h in history]

        # 2. Get AI recommendation
        ai_recommendation = None
        if ai and actions:
            ai_recommendation = ai.predict_next_product(actions, pids)

        # 3. Formulate Response using RAG
        response_text = ""
        suggested_products = []
        
        if ai_recommendation:
            top_ids = ai_recommendation['top_3']
            details = kb.get_product_details(top_ids)
            suggested_products = details
            
            main_prod = details[0] if details else None
            
            if trigger == 'cart':
                response_text = f"Tôi thấy bạn vừa thêm hàng vào giỏ. Dựa trên sở thích của bạn, có thể bạn sẽ thích '{main_prod['name']}' ({main_prod['category']}) đấy!"
            elif trigger == 'search':
                response_text = f"Kết quả tìm kiếm đây! Ngoài ra, hệ thống AI của tôi gợi ý bạn nên xem qua '{main_prod['name']}' vì nó rất hợp với phong cách của bạn."
            else:
                response_text = f"Chào bạn! Tôi đã phân tích lịch sử mua sắm của bạn. Bạn có muốn xem thử '{main_prod['name']}' không? Nó đang rất hot trong danh mục {main_prod['category']}."
        else:
            response_text = "Chào bạn! Tôi là trợ lý AI. Bạn cần tìm kiếm sản phẩm gì hôm nay?"

        return Response({
            "success": True,
            "reply": response_text,
            "recommendations": suggested_products,
            "actions_analyzed": len(actions)
        })

class ChatbotStatusView(APIView):
    def get(self, request):
        ai = get_ai_engine()
        return Response({
            "status": "online",
            "ai_loaded": ai is not None,
            "kb_connected": True
        })
