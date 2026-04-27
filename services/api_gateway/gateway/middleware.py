"""
Routing middleware for API Gateway
Forwards requests to appropriate microservices
"""
import requests
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json
import logging
import os

logger = logging.getLogger(__name__)


class RoutingMiddleware:
    """Route incoming requests to appropriate microservices"""
    
    # Service routing configuration
    ROUTES = {
        '/api/auth/': {
            'service': 'user-service',
            'url': os.getenv('USER_SERVICE_URL', 'http://user-service:8000'),
        },
        '/api/customer/': {
            'service': 'customer-service',
            'url': os.getenv('CUSTOMER_SERVICE_URL', 'http://customer-service:8000'),
        },
        '/api/products/': {
            'service': 'product-service',
            'url': os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000'),
        },
        '/api/cart/': {
            'service': 'cart-service',
            'url': os.getenv('CART_SERVICE_URL', 'http://cart-service:8000'),
        },
        '/api/orders/': {
            'service': 'order-service',
            'url': os.getenv('ORDER_SERVICE_URL', 'http://order-service:8000'),
        },
        '/api/payments/': {
            'service': 'payment-service',
            'url': os.getenv('PAYMENT_SERVICE_URL', 'http://payment-service:8000'),
        },
        '/api/vouchers/': {
            'service': 'voucher-service',
            'url': os.getenv('VOUCHER_SERVICE_URL', 'http://voucher-service:8000'),
        },
        '/api/ratings/': {
            'service': 'rating-service',
            'url': os.getenv('RATING_SERVICE_URL', 'http://rating-service:8000'),
        },
        '/api/suppliers/': {
            'service': 'supplier-service',
            'url': os.getenv('SUPPLIER_SERVICE_URL', 'http://supplier-service:8000'),
        },
        '/api/staff/': {
            'service': 'customer-service',
            'url': os.getenv('STAFF_SERVICE_URL', 'http://customer-service:8000'),
        },
        '/api/recommendations/': {
            'service': 'recommendation-service',
            'url': os.getenv('RECOMMENDATION_SERVICE_URL', 'http://recommendation-service:8001'),
        },
        '/api/chatbot/': {
            'service': 'chatbot-service',
            'url': os.getenv('CHATBOT_SERVICE_URL', 'http://chatbot-service:8000'),
        },
        '/api/tracking/': {
            'service': 'tracking-service',
            'url': os.getenv('TRACKING_SERVICE_URL', 'http://tracking-service:8000'),
        },
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request"""
        path = request.path
        print(f"ROUTING DEBUG: Incoming path is '{path}'")
        
        # Check if path should be routed
        route_config = self.get_route_config(path)
        
        if route_config:
            return self.forward_request(request, route_config)
        
        # Not a routable path, continue normally
        response = self.get_response(request)
        return response
    
    def get_route_config(self, path):
        """Get route configuration for path"""
        for prefix, config in self.ROUTES.items():
            if path.startswith(prefix):
                return config
        return None
    
    def forward_request(self, request, route_config):
        """Forward request to microservice"""
        try:
            # Build target URL
            internal_base_url = route_config['url'].rstrip('/')
            target_url = f"{internal_base_url}{request.path}"
            if request.GET:
                target_url += f"?{request.GET.urlencode()}"
            
            # Prepare headers - carefully filter
            headers = {}
            for key, value in request.headers.items():
                if key.lower() not in ['host', 'content-length', 'connection']:
                    headers[key] = value
            
            # Read body safely
            body = None
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                body = request.body
            
            # Forward with retries
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"DEBUG: Forwarding {request.method} {request.path} -> {target_url} (Attempt {attempt+1})")
                    response = requests.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        data=body,
                        timeout=15,
                        allow_redirects=False
                    )
                    
                    # Create Django response
                    django_response = HttpResponse(
                        content=response.content,
                        status=response.status_code,
                        content_type=response.headers.get('Content-Type', 'application/json')
                    )
                    
                    # Copy headers back
                    for key, value in response.headers.items():
                        if key.lower() not in ['content-encoding', 'transfer-encoding', 'content-length', 'connection']:
                            django_response[key] = value
                            
                    return django_response
                    
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"⚠️ Gateway Forwarding Error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        return JsonResponse({
                            'success': False, 
                            'error': f'Service {route_config["service"]} unreachable',
                            'details': str(e)
                        }, status=503)
            
            return JsonResponse({'success': False, 'error': 'Gateway timeout'}, status=504)
            
            return JsonResponse({'success': False, 'error': 'Max retries reached'}, status=503)
            
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal gateway error',
                'details': str(e)
            }, status=500)
