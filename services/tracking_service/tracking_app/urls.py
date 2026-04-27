from django.urls import path
from .views import LogSearchView, LogProductView, GetStatsView, LogCartActionView, GetUserHistoryView, LogPurchaseView

urlpatterns = [
    path('log-search/', LogSearchView.as_view(), name='log-search'),
    path('log-view/', LogProductView.as_view(), name='log-view'),
    path('log-cart/', LogCartActionView.as_view(), name='log-cart'),
    path('log-purchase/', LogPurchaseView.as_view(), name='log-purchase'),
    path('stats/', GetStatsView.as_view(), name='stats'),
    path('user-history/<int:customer_id>/', GetUserHistoryView.as_view(), name='user-history'),
]
