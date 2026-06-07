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
from .application.use_cases import VoucherUseCases
from .domain.exceptions import VoucherValidationError
from .infrastructure.repositories import DjangoVoucherRepository
from .presentation.serializers import voucher_to_dict, voucher_validation_to_dict


voucher_use_cases = VoucherUseCases(DjangoVoucherRepository())

@csrf_exempt
@require_http_methods(["GET"])
def list_active_vouchers(request):
    """List all currently active global vouchers"""
    vouchers = voucher_use_cases.list_active()
    return JsonResponse({
        'success': True,
        'data': [voucher_to_dict(v) for v in vouchers]
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
            
        voucher, discount = voucher_use_cases.validate(request.user_id, code, order_amount)
        
        return JsonResponse({
            'success': True,
            'data': voucher_validation_to_dict(voucher, order_amount, discount)
        })
    except Voucher.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid voucher code'}, status=404)
    except VoucherValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff'])
def create_voucher(request):
    """Staff only: Create a new voucher"""
    try:
        data = json.loads(request.body)
        voucher = voucher_use_cases.create(data)
        return JsonResponse({
            'success': True,
            'message': 'Voucher created',
            'data': voucher_to_dict(voucher)
        }, status=201)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
