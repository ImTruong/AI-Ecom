import os
import requests
import json

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class FreeLLMClient:
    def __init__(self):
        # Allow reading from environment variable
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            print("[GEMINI] API key missing.")

    def chat_with_context(self, user_message, context_data, trigger):
        if not self.api_key:
            print("[GEMINI] No API key set.")
            return None

        system_instruction = (
            "Bạn là trợ lý mua sắm thông minh của TruongShop. "
            "Hãy trả lời người dùng thân thiện bằng tiếng Việt.\n"
            f"- Lịch sử xem/mua hàng: {context_data.get('history', [])}\n"
            f"- AI đề xuất chính: {context_data.get('ai_prediction', 'Chưa có')}\n"
            f"- Gợi ý mua sắm từ AI: {context_data.get('ai_suggestions', [])}\n"
            f"- Top hàng bán chạy: {context_data.get('top_products', [])}\n"
            f"- Voucher khả dụng: {context_data.get('vouchers', [])}\n"
            f"- Thông tin chính sách cửa hàng / FAQ liên quan: {context_data.get('kb_context', 'Không có')}\n\n"
            "Yêu cầu:\n"
            "1. Nếu người dùng hỏi lịch sử, hãy liệt kê lịch sử.\n"
            "2. Nếu có thông tin chính sách/FAQ liên quan, hãy sử dụng thông tin đó để trả lời câu hỏi của người dùng một cách chính xác.\n"
            "3. Nếu người dùng hỏi về gợi ý sản phẩm, hãy giới thiệu các gợi ý mua sắm từ AI ở trên.\n"
            "4. Trả lời tự nhiên, tránh máy móc, hãy là một trợ lý bán hàng lịch sự và tận tâm."
        )

        prompt = f"{system_instruction}\n\nNgười dùng: {user_message}\nTrigger: {trigger}"

        try:
            url = f"{GEMINI_API_URL}?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                print(f"[GEMINI] API error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"[GEMINI] Exception occurred: {e}")
            return None


_freellm_instance = None


def get_freellm_client():
    global _freellm_instance
    if _freellm_instance is None:
        _freellm_instance = FreeLLMClient()
    return _freellm_instance
