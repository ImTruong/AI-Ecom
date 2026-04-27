from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Voucher, VoucherUsage
from django.utils import timezone
import json
import sys
import os

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from jwt_utils import jwt_required

@csrf_exempt
@require_http_methods(["GET"])
def list_active_vouchers(request):
    """List all currently active global vouchers"""
    now = timezone.now()
    vouchers = Voucher.objects.filter(
        is_active=True,
        is_global=True,
        start_date__lte=now,
        end_date__gte=now
    )
    return JsonResponse({
        'success': True,
        'data': [v.to_dict() for v in vouchers]
    })

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def validate_voucher(request):
    """Validate a voucher code against an order amount"""
    try:
        data = json.loads(request.body)
        code = data.get('code')
        order_amount = data.get('order_amount', 0)
        
        if not code:
            return JsonResponse({'success': False, 'error': 'Voucher code required'}, status=400)
            
        try:
            voucher = Voucher.objects.get(code=str(code).strip().upper())
        except Voucher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid voucher code'}, status=404)
            
        if not voucher.is_valid(float(order_amount)):
            return JsonResponse({'success': False, 'error': 'Voucher is not valid for this order amount'}, status=400)
            
        # Check if user already used this non-global voucher
        if not voucher.is_global:
            if VoucherUsage.objects.filter(voucher=voucher, customer_id=request.user_id).exists():
                return JsonResponse({'success': False, 'error': 'You have already used this voucher'}, status=400)
                
        discount = voucher.calculate_discount(float(order_amount))
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': voucher.id,
                'code': voucher.code,
                'discount_applied': float(discount),
                'new_total': float(order_amount) - float(discount)
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff'])
def create_voucher(request):
    """Staff only: Create a new voucher"""
    try:
        data = json.loads(request.body)
        voucher = Voucher.objects.create(
            code=data.get('code').upper(),
            name=data.get('name'),
            description=data.get('description', ''),
            discount_type=data.get('discount_type'),
            discount_value=data.get('discount_value'),
            min_order_value=data.get('min_order_value', 0),
            max_discount=data.get('max_discount'),
            start_date=data.get('start_date', timezone.now()),
            end_date=data.get('end_date'),
            usage_limit=data.get('usage_limit'),
            is_global=data.get('is_global', True)
        )
        return JsonResponse({
            'success': True,
            'message': 'Voucher created',
            'data': voucher.to_dict()
        }, status=201)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
