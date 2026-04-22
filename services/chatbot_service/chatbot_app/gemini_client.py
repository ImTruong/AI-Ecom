import google.generativeai as genai
import os

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            print("[GEMINI] Configuring with provided API Key...")
            genai.configure(api_key=self.api_key)
            # Switch to 1.5-flash: more robust, faster, and supported in all regions
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("[GEMINI] API Key missing in environment.")
            self.model = None

    def chat_with_context(self, user_message, context_data, trigger):
        if not self.model:
            return None
        
        system_instruction = (
            "Bạn là trợ lý mua sắm thông minh của TruongShop. "
            "Hãy trả lời người dùng cực kỳ thân thiện bằng tiếng Việt. "
            "Bối cảnh người dùng:\n"
            f"- Lịch sử: {context_data.get('history', [])}\n"
            f"- AI đề xuất: {context_data.get('ai_prediction', 'Chưa có')}\n"
            f"- Top hàng bán chạy: {context_data.get('top_products', [])}\n\n"
            "Yêu cầu:\n"
            "1. Nếu người dùng hỏi 'tôi vừa xem gì' hoặc 'lịch sử', hãy liệt kê từ mục Lịch sử.\n"
            "2. Luôn ưu tiên dùng tiếng Việt tự nhiên.\n"
            "3. Nếu không có lịch sử, hãy gợi ý các sản phẩm hot.\n"
            "4. Đừng trả lời quá máy móc."
        )

        prompt = f"{system_instruction}\n\nNgười dùng: {user_message}\nTrigger: {trigger}"

        try:
            response = self.model.generate_content(prompt)
            # Robust extraction of text
            if response and response.candidates:
                return response.text
            return "Xin lỗi, tôi gặp chút trục trặc khi suy nghĩ. Bạn cần tôi giúp gì?"
        except Exception as e:
            print(f"[GEMINI] API Error: {e}")
            return None

# Singleton
_gemini_instance = None
def get_gemini_client():
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiClient()
    return _gemini_instance
