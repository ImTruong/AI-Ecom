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
        '/api/laptop/': {
            'service': 'laptop-service',
            'url': os.getenv('LAPTOP_SERVICE_URL', 'http://laptop-service:8000'),
        },
        '/api/phone/': {
            'service': 'phone-service',
            'url': os.getenv('PHONE_SERVICE_URL', 'http://phone-service:8000'),
        },
        '/api/tablet/': {
            'service': 'tablet-service',
            'url': os.getenv('TABLET_SERVICE_URL', 'http://tablet-service:8000'),
        },
        '/api/camera/': {
            'service': 'camera-service',
            'url': os.getenv('CAMERA_SERVICE_URL', 'http://camera-service:8000'),
        },
        '/api/headphone/': {
            'service': 'headphone-service',
            'url': os.getenv('HEADPHONE_SERVICE_URL', 'http://headphone-service:8000'),
        },
        '/api/watch/': {
            'service': 'watch-service',
            'url': os.getenv('WATCH_SERVICE_URL', 'http://watch-service:8000'),
        },
        '/api/shoe/': {
            'service': 'shoe-service',
            'url': os.getenv('SHOE_SERVICE_URL', 'http://shoe-service:8000'),
        },
        '/api/furniture/': {
            'service': 'furniture-service',
            'url': os.getenv('FURNITURE_SERVICE_URL', 'http://furniture-service:8000'),
        },
        '/api/tracking/': {
            'service': 'tracking-service',
            'url': os.getenv('TRACKING_SERVICE_URL', 'http://tracking-service:8000'),
        },
        '/api/recommendations/': {
            'service': 'recommendation-service',
            'url': os.getenv('RECOMMENDATION_SERVICE_URL', 'http://recommendation-service:8001'),
        },
        '/api/ai-chat/': {
            'service': 'recommendation-service',
            'url': os.getenv('RECOMMENDATION_SERVICE_URL', 'http://recommendation-service:8001'),
        },
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request"""
        path = request.path
        print(f"ROUTING DEBUG: Incoming path is '{path}'")

        # Special Case: Aggregating products from 10 distributed services
        if path == '/api/products/' and request.method == 'GET':
            return self.aggregate_products(request)
        
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

    def aggregate_products(self, request):
        """Aggregator: Fetch products from 10 category services in parallel"""
        from concurrent.futures import ThreadPoolExecutor
        
        services = [
            'book-service', 'clothes-service', 'laptop-service', 'phone-service',
            'tablet-service', 'camera-service', 'headphone-service', 'watch-service',
            'shoe-service', 'furniture-service', 'product-service'
        ]
        
        def fetch_service_products(service_name):
            try:
                url = f"http://{service_name}:8000/api/products/"
                # Forward query params if any
                if request.GET:
                    url += f"?{request.GET.urlencode()}"
                
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                logger.error(f"Error fetching from {service_name}: {e}")
            return []

        all_products = []
        with ThreadPoolExecutor(max_workers=len(services)) as executor:
            # Fetch all in parallel
            results = list(executor.map(fetch_service_products, services))
            for res in results:
                if isinstance(res, list):
                    all_products.extend(res)

        return JsonResponse(all_products, safe=False)
    
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
            
            # Forward relevant headers.
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
