from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
import os
import sys
from django.db import transaction
from .models import Order, OrderItem

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from jwt_utils import jwt_required

CART_SERVICE_URL = os.getenv('CART_SERVICE_URL', 'http://cart-service:8000')
CUSTOMER_SERVICE_URL = os.getenv('CUSTOMER_SERVICE_URL', 'http://customer-service:8000')
VOUCHER_SERVICE_URL = os.getenv('VOUCHER_SERVICE_URL', 'http://voucher-service:8000')

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def place_order(request):
    """Place a new order"""
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')
        payment_method = data.get('payment_method', 'cod')
        voucher_code = data.get('voucher_code')
        
        if not address_id:
            return JsonResponse({'success': False, 'error': 'Shipping address required'}, status=400)
            
        # 1. Get Cart
        auth_header = {'Authorization': request.headers.get('Authorization')}
        cart_resp = requests.get(f"{CART_SERVICE_URL}/api/cart/", headers=auth_header)
        if not cart_resp.ok:
            return JsonResponse({'success': False, 'error': 'Failed to retrieve cart'}, status=500)
            
        cart_json = cart_resp.json()
        cart_info = cart_json.get('data', {})
        cart_items = cart_info.get('items', [])
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)
            
        # 2. Get Shipping Address
        addr_resp = requests.get(f"{CUSTOMER_SERVICE_URL}/api/customer/address/", headers=auth_header)
        if not addr_resp.ok:
            return JsonResponse({'success': False, 'error': 'Failed to retrieve addresses'}, status=500)
            
        addresses = addr_resp.json().get('data', [])
        shipping_addr = next((a for a in addresses if a['id'] == address_id), None)
        if not shipping_addr:
            return JsonResponse({'success': False, 'error': 'Invalid shipping address'}, status=400)
            
        # 3. Calculate Totals
        total_amount = sum(float(item['price']) * int(item['quantity']) for item in cart_items)
        discount_amount = 0
        
        # 4. Handle Voucher
        if voucher_code:
            v_resp = requests.post(f"{VOUCHER_SERVICE_URL}/api/vouchers/validate/", 
                                 headers=auth_header, 
                                 json={'code': voucher_code, 'order_amount': float(total_amount)})
            if v_resp.ok:
                v_data = v_resp.json().get('data', {})
                discount_amount = v_data.get('discount_applied', 0)
                
        final_amount = float(total_amount) - float(discount_amount)
        
        # 5. Create Order
        with transaction.atomic():
            order = Order.objects.create(
                customer_id=request.user_id,
                total_amount=total_amount,
                discount_amount=discount_amount,
                final_amount=final_amount,
                voucher_code=voucher_code,
                payment_method=payment_method,
                shipping_address_id=address_id,
                shipping_full_name=shipping_addr['full_name'],
                shipping_phone=shipping_addr['phone'],
                shipping_address_line=shipping_addr['address_line']
            )
            
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_type=item['product_type'],
                    product_id=item['product_id'],
                    product_name=item.get('name', f"{item['product_type']} #{item['product_id']}"),
                    price=float(item['price']),
                    quantity=int(item['quantity'])
                )
        
        # 6. Deduct Stock from unified product service
        PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000')
        TRACKING_SERVICE_URL = os.getenv('TRACKING_SERVICE_URL', 'http://tracking-service:8000')
        
        for item in cart_items:
            try:
                # Use negative quantity to subtract from stock
                requests.post(f"{PRODUCT_SERVICE_URL}/api/products/update-stock/", json={
                    'variant_id': item['product_id'],
                    'quantity': -int(item['quantity'])
                })
            except Exception as se:
                print(f"Error deducting stock for item {item['product_id']}: {se}")

        # 7. Notify Tracking Service (Rank 5.0 behavior)
        try:
            requests.post(f"{TRACKING_SERVICE_URL}/api/tracking/log-purchase/", json={
                'customer_id': request.user_id,
                'order_id': order.id,
                'items': [
                    {'product_id': item['product_id'], 'product_type': item['product_type'], 'price': item['price'], 'quantity': item['quantity']}
                    for item in cart_items
                ]
            })
        except Exception as te:
            print(f"Tracking notification failed: {te}")

        # 8. Clear Cart
        requests.delete(f"{CART_SERVICE_URL}/api/cart/clear/", headers=auth_header)
        
        return JsonResponse({
            'success': True,
            'message': 'Order placed successfully and stock updated',
            'data': order.to_dict()
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def list_my_orders(request):
    """List orders for current customer"""
    orders = Order.objects.filter(customer_id=request.user_id).order_by('-created_at')
    return JsonResponse({
        'success': True,
        'data': [o.to_dict() for o in orders]
    })

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_order_detail(request, order_id):
    """Get order details"""
    try:
        order = Order.objects.get(id=order_id, customer_id=request.user_id)
        return JsonResponse({
            'success': True,
            'data': order.to_dict()
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['staff'])
def list_all_orders(request):
    """List all orders for staff"""
    orders = Order.objects.all().order_by('-created_at')
    return JsonResponse({
        'success': True,
        'data': [o.to_dict() for o in orders]
    })

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['staff', 'customer']) # Customer might want to see stats but staff definitely needs it
def get_order_stats(request):
    """Get order statistics for dashboard"""
    total = Order.objects.count()
    pending = Order.objects.filter(status='pending').count()
    delivered = Order.objects.filter(status='delivered').count()
    shipping = Order.objects.filter(status='shipping').count()
    
    return JsonResponse({
        'success': True,
        'data': {
            'total': total,
            'pending': pending,
            'delivered': delivered,
            'shipping': shipping
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff'])
def update_order_status(request):
    """Update order status (Staff only)"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Order ID and status required'}, status=400)
            
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Order #{order_id} status updated to {new_status}',
            'data': order.to_dict()
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
