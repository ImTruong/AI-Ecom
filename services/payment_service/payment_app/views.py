from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import os
import sys
from .models import Payment

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from jwt_utils import jwt_required

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
            
        # In a real app, integrate with gateway (Stripe/PayPal) here
        
        # Simulate local success for COD or Banking
        status = Payment.PaymentStatus.COMPLETED
        if payment_method == 'cod':
            # COD is pending until physical delivery, but we record it
            status = Payment.PaymentStatus.PENDING
            
        payment = Payment.objects.create(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            status=status,
            transaction_id=f"TXN-{order_id}-{int(os.times()[4])}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Payment record created',
            'data': payment.to_dict()
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_payment_status(request, order_id):
    """Get status of a payment"""
    try:
        payment = Payment.objects.get(order_id=order_id)
        return JsonResponse({
            'success': True,
            'data': payment.to_dict()
        })
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'}, status=404)
