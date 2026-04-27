import random

class LocalBrain:
    def __init__(self):
        self.name = "TruongShop AI"

    def synthesize(self, user_message, context, trigger):
        history = context.get('history', [])
        prediction = context.get('ai_prediction', 'Không có')
        top_products = context.get('top_products', [])
        
        msg = user_message.lower()
        
        # 1. Dynamic History Responses
        if any(kw in msg for kw in ["xem j", "xem gì", "vừa xem", "đã xem", "lịch sử"]):
            if history:
                items = [h.split(" ", 1)[1] for h in history if " " in h]
                recent = list(dict.fromkeys(items))[-3:]
                return f"Bạn đã xem qua: {', '.join(recent)}. Bạn cần tôi tìm thêm thông tin về sản phẩm nào trong số này không?"
            return "Bạn chưa có lịch sử xem hàng trong phiên này."

        # 2. Dynamic Gợi ý / Prediction
        if any(kw in msg for kw in ["gợi ý", "nên mua", "tư vấn", "recommend"]):
            if prediction and prediction != "Không có":
                return f"Theo thuật toán AI của tôi, bạn nên cân nhắc sản phẩm '{prediction}'. Ngoài ra, các sản phẩm hot khác bao gồm: {', '.join(top_products[:2])}."
            if top_products:
                return f"Tôi gợi ý bạn xem qua: {', '.join(top_products[:3])}. Đây là những món đang được quan tâm nhiều nhất."

        # 3. Trigger Handling (Cart / View)
        if trigger == 'cart':
            suggestion = f" và '{top_products[0]}'" if top_products else ""
            return f"Đã thêm vào giỏ hàng! Có thể bạn sẽ quan tâm đến {suggestion} để mua cùng."

        # 4. Default / Greeting
        return "Chào bạn! Tôi là trợ lý AI. Tôi có thể giúp bạn xem lại lịch sử hoặc gợi ý sản phẩm phù hợp nhất với bạn."

_brain_instance = None
def get_local_brain():
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = LocalBrain()
    return _brain_instance
