from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import sys
from .models import Payment, PaymentLog, PaymentMethod
from .application.use_cases import PaymentUseCases
from .infrastructure.repositories import DjangoPaymentRepository
from .presentation.serializers import payment_log_to_dict, payment_method_to_dict, payment_to_dict

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from jwt_utils import jwt_required
payment_use_cases = PaymentUseCases(DjangoPaymentRepository())

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def process_payment(request):
    """Process a payment for an order (Simulation)"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'cod')
        
        if not order_id or not amount:
            return JsonResponse({'success': False, 'error': 'Order ID and amount required'}, status=400)
            
        payment = payment_use_cases.process_payment(data)
        
        return JsonResponse({
            'success': True,
            'message': 'Payment record created',
            'data': payment_to_dict(payment)
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_payment_status(request, order_id):
    """Get status of a payment"""
    try:
        payment = payment_use_cases.get_payment_status(order_id)
        return JsonResponse({
            'success': True,
            'data': payment_to_dict(payment)
        })
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'}, status=404)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer', 'staff'])
def list_payment_methods(request):
    methods = payment_use_cases.list_payment_methods()
    return JsonResponse({'success': True, 'data': [payment_method_to_dict(method) for method in methods]})


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['staff'])
def list_payment_logs(request, payment_id):
    logs = payment_use_cases.list_payment_logs(payment_id)
    return JsonResponse({'success': True, 'data': [payment_log_to_dict(log) for log in logs]})
