"""
Cart views
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import sys
import os
import requests

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from jwt_utils import jwt_required
from .models import Cart, CartItem
from .application.use_cases import CartUseCases
from .domain.exceptions import CartValidationError
from .infrastructure.repositories import DjangoCartRepository
from .presentation.serializers import cart_to_dict


cart_use_cases = CartUseCases(DjangoCartRepository())


@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_cart(request):
    """Get customer's cart"""
    try:
        # The jwt_required decorator attaches user_id to the request
        customer_id = request.user_id
        
        cart = cart_use_cases.get_cart(customer_id)
        
        return JsonResponse({
            'success': True,
            'data': cart_to_dict(cart)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def add_to_cart(request):
    """Add item to cart"""
    try:
        customer_id = request.user_id
        data = json.loads(request.body)
        
        required_fields = ['product_type', 'product_id', 'variant_id', 'price']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        quantity = data.get('quantity', 1)
        cart, item_created = cart_use_cases.add_to_cart(customer_id, data)
        try:
            tracking_url = os.getenv('TRACKING_SERVICE_URL', 'http://tracking-service:8000')
            requests.post(f"{tracking_url}/api/tracking/add-to-cart/", json={
                'customer_id': customer_id,
                'product_id': data['product_id'],
                'product_variant_id': data.get('variant_id'),
                'product_type': data['product_type'],
                'action_type': 'add',
                'quantity': quantity,
                'price': str(data['price']),
            }, timeout=2)
        except Exception:
            pass
        
        return JsonResponse({
            'success': True,
            'data': cart_to_dict(cart),
            'message': 'Item added to cart'
        }, status=201 if item_created else 200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except CartValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def update_cart_item(request):
    """Update cart item quantity"""
    try:
        customer_id = request.user_id
        data = json.loads(request.body)
        
        required_fields = ['product_type', 'product_id', 'variant_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        cart = cart_use_cases.update_quantity(customer_id, data)
        
        return JsonResponse({
            'success': True,
            'data': cart_to_dict(cart),
            'message': 'Cart item updated'
        })
    
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart not found'
        }, status=404)
    
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        }, status=404)
    except CartValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['customer'])
def remove_from_cart(request, product_type, product_id):
    """Remove item from cart"""
    try:
        customer_id = request.user_id
        variant_id = request.GET.get('variant_id')
        cart = cart_use_cases.remove_from_cart(customer_id, product_type, product_id, variant_id)
        
        return JsonResponse({
            'success': True,
            'data': cart_to_dict(cart),
            'message': 'Item removed from cart'
        })
    
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart not found'
        }, status=404)
    
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        }, status=404)
    except CartValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['customer'])
def clear_cart(request):
    """Clear all items from cart"""
    try:
        customer_id = request.user_id
        
        cart = cart_use_cases.clear_cart(customer_id)
        
        return JsonResponse({
            'success': True,
            'data': cart_to_dict(cart),
            'message': 'Cart cleared'
        })
    
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
