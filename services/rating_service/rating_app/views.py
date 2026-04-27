from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
from django.conf import settings
from jwt_utils import jwt_required
from .models import Rating

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def add_rating(request):
    """Add a rating for a specific item in a delivered order"""
    try:
        data = json.loads(request.body)
        print(f"RATING DEBUG: Received submission data: {data}")
        order_id = data.get('order_id')
        product_type = data.get('product_type')
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        stars = data.get('stars')
        comment = data.get('comment', '')

        if not all([order_id, product_type, product_id, stars]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        if not (1 <= int(stars) <= 5):
            return JsonResponse({'success': False, 'error': 'Stars must be between 1 and 5'}, status=400)

        # 1. Verify order belongs to user and is delivered
        try:
            headers = {'Authorization': request.META.get('HTTP_AUTHORIZATION')}
            order_resp = requests.get(f"{settings.ORDER_SERVICE_URL}/api/orders/{order_id}/", headers=headers, timeout=5)
            
            if order_resp.status_code != 200:
                return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
            
            order_data = order_resp.json()
            if not order_data.get('success'):
                return JsonResponse({'success': False, 'error': 'Could not fetch order data'}, status=500)
            
            order = order_data.get('data')
            if order.get('status') != 'delivered':
                return JsonResponse({'success': False, 'error': 'You can only rate delivered orders'}, status=400)
            
            if order.get('customer_id') != request.user_id:
                return JsonResponse({'success': False, 'error': 'Unauthorized access to this order'}, status=403)
            
            # Verify item exists in order
            item_exists = any(
                str(item['product_id']) == str(product_id) and item['product_type'] == product_type 
                for item in order.get('items', [])
            )
            
            if not item_exists:
                return JsonResponse({'success': False, 'error': 'Product not found in this order'}, status=400)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'success': False, 'error': f'Order service communication error: {str(e)}'}, status=503)

        # 2. Check if already rated
        if Rating.objects.filter(order_id=order_id, product_type=product_type, product_id=product_id).exists():
            return JsonResponse({'success': False, 'error': 'You have already rated this item in this order'}, status=400)

        # 3. Create rating
        rating = Rating.objects.create(
            order_id=order_id,
            customer_id=request.user_id,
            product_type=product_type,
            product_id=product_id,
            product_name=product_name,
            stars=stars,
            comment=comment
        )

        return JsonResponse({
            'success': True,
            'message': 'Rating added successfully',
            'data': rating.to_dict()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_product_ratings(request, product_type, product_id):
    """Get all ratings for a specific product"""
    ratings = Rating.objects.filter(product_type=product_type, product_id=product_id).order_by('-created_at')
    return JsonResponse({
        'success': True,
        'data': [r.to_dict() for r in ratings]
    })

@csrf_exempt
@require_http_methods(["GET"])
def list_all_ratings(request):
    """List all ratings (for efficient homepage aggregate calculations)"""
    try:
        ratings = Rating.objects.all().order_by('-created_at')
        return JsonResponse({
            'success': True,
            'data': [r.to_dict() for r in ratings]
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_order_ratings(request, order_id):
    """Get ratings made for a specific order"""
    ratings = Rating.objects.filter(order_id=order_id, customer_id=request.user_id)
    return JsonResponse({
        'success': True,
        'data': [r.to_dict() for r in ratings]
    })
