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
            'service': 'auth-service',
            'url': os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8000'),
        },
        '/api/customer/': {
            'service': 'customer-service',
            'url': os.getenv('CUSTOMER_SERVICE_URL', 'http://customer-service:8000'),
        },
        '/api/books/': {
            'service': 'book-service',
            'url': os.getenv('BOOK_SERVICE_URL', 'http://book-service:8000'),
        },
        '/api/clothes/': {
            'service': 'clothes-service',
            'url': os.getenv('CLOTHES_SERVICE_URL', 'http://clothes-service:8000'),
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
            target_url = route_config['url'] + request.path
            
            if request.GET:
                query_string = request.GET.urlencode()
                target_url += f'?{query_string}'
            
            # Prepare headers
            headers = {}
            
            # Forward Authorization header if present
            if 'HTTP_AUTHORIZATION' in request.META:
                headers['Authorization'] = request.META['HTTP_AUTHORIZATION']
            
            # Forward Content-Type
            if 'CONTENT_TYPE' in request.META:
                headers['Content-Type'] = request.META['CONTENT_TYPE']
            
            # Prepare body
            body = None
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                try:
                    body = request.body
                except Exception as e:
                    logger.error(f"Error reading request body: {e}")
            
            # Make request to microservice
            logger.info(f"Forwarding {request.method} {request.path} to {target_url}")
            print(f"FORWARDING: {request.method} {request.path} -> {target_url}")
            
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
                timeout=30,
                allow_redirects=False
            )
            
            # Create Django response from microservice response
            django_response = HttpResponse(
                content=response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )
            
            # Forward relevant headers. Note: Content-Length should NOT be forwarded manually
            # as Django will calculate it correctly based on the content provided.
            if 'Content-Type' in response.headers:
                django_response['Content-Type'] = response.headers['Content-Type']
            
            return django_response
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {route_config['service']}: {e}")
            return JsonResponse({
                'success': False,
                'error': f"Service {route_config['service']} is unavailable"
            }, status=503)
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {route_config['service']}: {e}")
            return JsonResponse({
                'success': False,
                'error': f"Service {route_config['service']} timed out"
            }, status=504)
        
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal gateway error'
            }, status=500)
