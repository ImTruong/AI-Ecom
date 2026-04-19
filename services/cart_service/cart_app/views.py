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

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from jwt_utils import jwt_required
from .models import Cart, CartItem


@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_cart(request):
    """Get customer's cart"""
    try:
        # The jwt_required decorator attaches user_id to the request
        customer_id = request.user_id
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(customer_id=customer_id)
        
        return JsonResponse({
            'success': True,
            'data': cart.to_dict()
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
        
        # Validate required fields
        required_fields = ['product_type', 'product_id', 'price']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Validate REQUIRED_TYPES
        VALID_TYPES = ['laptop', 'phone', 'book', 'clothes', 'watch', 'camera', 'shoe', 'furniture', 'tablet', 'headphone']
        if data['product_type'] not in VALID_TYPES:
            # Try to sanitize (e.g., 'books' -> 'book')
            sanitized = data['product_type'].rstrip('s')
            if sanitized in VALID_TYPES:
                data['product_type'] = sanitized
            else:
                return JsonResponse({
                    'success': False,
                    'error': f"Invalid product_type: {data['product_type']}. Must be one of {VALID_TYPES}"
                }, status=400)
        
        quantity = data.get('quantity', 1)
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be at least 1'
            }, status=400)
        
        with transaction.atomic():
            # Get or create cart
            cart, created = Cart.objects.get_or_create(customer_id=customer_id)
            
            # Check if item already in cart
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product_type=data['product_type'],
                product_id=data['product_id'],
                defaults={
                    'price': data['price'],
                    'product_name': data.get('product_name'),
                    'image_url': data.get('image_url'),
                    'quantity': quantity
                }
            )
            
            if not item_created:
                # Item exists, update quantity
                cart_item.quantity += quantity
                cart_item.price = data['price']
                if data.get('product_name'): cart_item.product_name = data.get('product_name')
                if data.get('image_url'): cart_item.image_url = data.get('image_url')
                cart_item.save()
        
        # Reload cart to get updated data
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'data': cart.to_dict(),
            'message': 'Item added to cart'
        }, status=201 if item_created else 200)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
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
        
        # Validate required fields
        required_fields = ['product_type', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        quantity = data['quantity']
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be at least 1'
            }, status=400)
        
        with transaction.atomic():
            cart = Cart.objects.get(customer_id=customer_id)
            cart_item = CartItem.objects.get(
                cart=cart,
                product_type=data['product_type'],
                product_id=data['product_id']
            )
            
            cart_item.quantity = quantity
            cart_item.save()
        
        # Reload cart
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'data': cart.to_dict(),
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
        
        with transaction.atomic():
            cart = Cart.objects.get(customer_id=customer_id)
            cart_item = CartItem.objects.get(
                cart=cart,
                product_type=product_type,
                product_id=product_id
            )
            
            cart_item.delete()
        
        # Reload cart
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'data': cart.to_dict(),
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
        
        with transaction.atomic():
            cart = Cart.objects.get(customer_id=customer_id)
            cart.items.all().delete()
        
        # Reload cart
        cart.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'data': cart.to_dict(),
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
