import os
import requests

FREELLM_ENDPOINT = "https://apifreellm.com/api/v1/chat"


class FreeLLMClient:
    def __init__(self):
        self.api_key = os.getenv("FREELLM_API_KEY")
        if not self.api_key:
            print("[FREELLM] API key missing in environment.")

    def chat_with_context(self, user_message, context_data, trigger):
        if not self.api_key:
            return None

        system_instruction = (
            "Bạn là trợ lý mua sắm thông minh của TruongShop. "
            "Hãy trả lời người dùng thân thiện bằng tiếng Việt.\n"
            f"- Lịch sử: {context_data.get('history', [])}\n"
            f"- AI đề xuất: {context_data.get('ai_prediction', 'Chưa có')}\n"
            f"- Gợi ý AI: {context_data.get('ai_suggestions', [])}\n"
            f"- Top hàng bán chạy: {context_data.get('top_products', [])}\n"
            f"- Voucher khả dụng: {context_data.get('vouchers', [])}\n\n"
            "Yêu cầu:\n"
            "1. Nếu người dùng hỏi lịch sử, hãy liệt kê lịch sử.\n"
            "2. Nếu không có lịch sử, hãy gợi ý sản phẩm hot và voucher.\n"
            "3. Trả lời tự nhiên, tránh máy móc."
        )

        prompt = f"{system_instruction}\n\nNgười dùng: {user_message}\nTrigger: {trigger}"

        response = requests.post(
            FREELLM_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            json={
                "message": prompt,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"[FREELLM] API error {response.status_code}: {response.text}")
            return None

        payload = response.json()
        if payload.get("success"):
            return payload.get("response")
        return None


_freellm_instance = None


def get_freellm_client():
    global _freellm_instance
    if _freellm_instance is None:
        _freellm_instance = FreeLLMClient()
    return _freellm_instance
