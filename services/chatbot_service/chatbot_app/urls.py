from django.urls import path
from .views import ChatbotAIView, ChatbotStatusView

urlpatterns = [
    path('ask/', ChatbotAIView.as_view(), name='chatbot_ask'),
    path('status/', ChatbotStatusView.as_view(), name='chatbot_status'),
]
