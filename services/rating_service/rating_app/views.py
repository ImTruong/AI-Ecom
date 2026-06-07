from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
from django.conf import settings
from jwt_utils import jwt_required
from .models import Rating
from .application.use_cases import RatingUseCases
from .domain.exceptions import RatingValidationError
from .infrastructure.repositories import DjangoRatingRepository
from .presentation.serializers import rating_to_dict


rating_use_cases = RatingUseCases(DjangoRatingRepository())

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
        stars = data.get('stars')

        if not all([order_id, product_type, product_id, stars]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

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

        except requests.exceptions.RequestException as e:
            return JsonResponse({'success': False, 'error': f'Order service communication error: {str(e)}'}, status=503)

        rating = rating_use_cases.add_rating(request.user_id, data, order)

        return JsonResponse({
            'success': True,
            'message': 'Rating added successfully',
            'data': rating_to_dict(rating)
        })

    except PermissionError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)
    except RatingValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_product_ratings(request, product_type, product_id):
    """Get all ratings for a specific product"""
    ratings = Rating.objects.filter(product_type=product_type, product_id=product_id).order_by('-created_at')
    return JsonResponse({
        'success': True,
        'data': [rating_to_dict(r) for r in ratings]
    })

@csrf_exempt
@require_http_methods(["GET"])
def list_all_ratings(request):
    """List all ratings (for efficient homepage aggregate calculations)"""
    try:
        ratings = Rating.objects.all().order_by('-created_at')
        return JsonResponse({
            'success': True,
            'data': [rating_to_dict(r) for r in ratings]
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
        'data': [rating_to_dict(r) for r in ratings]
    })
