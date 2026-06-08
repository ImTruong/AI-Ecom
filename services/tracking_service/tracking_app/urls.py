from django.urls import path
from .views import (
    LogCartActionView,
    LogProductView,
    LogPurchaseView,
    LogTrackingEventView,
    GetStatsView,
    GetUserHistoryView,
)

urlpatterns = [
    path('log-view/', LogProductView.as_view(), name='log-view'),
    path('click-product/', LogProductView.as_view(), name='click-product'),
    path('log-cart/', LogCartActionView.as_view(), name='log-cart'),
    path('add-to-cart/', LogCartActionView.as_view(), name='add-to-cart'),
    path('log-purchase/', LogPurchaseView.as_view(), name='log-purchase'),
    path('place-order/', LogPurchaseView.as_view(), name='place-order'),
    path('events/', LogTrackingEventView.as_view(), name='tracking-events'),
    path('stats/', GetStatsView.as_view(), name='stats'),
    path('user-history/<int:customer_id>/', GetUserHistoryView.as_view(), name='user-history'),
]
