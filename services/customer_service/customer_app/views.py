"""
Customer views
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
from .models import Customer, ShippingAddress


@require_http_methods(["GET"])
@jwt_required(user_types=['customer'])
def get_profile(request):
    """Get customer profile"""
    try:
        # The jwt_required decorator attaches user_id to the request
        auth_customer_id = request.user_id
        
        customer = Customer.objects.get(auth_customer_id=auth_customer_id)
        
        return JsonResponse({
            'success': True,
            'data': {
                **customer.to_dict(),
                'addresses': [addr.to_dict() for addr in customer.shipping_addresses.all()]
            }
        })
    
    except Customer.DoesNotExist:
        # Customer not synced yet from auth service
        return JsonResponse({
            'success': False,
            'error': 'Customer profile not found. Please try again later.'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
@jwt_required(user_types=['customer'])
def update_profile(request):
    """Update customer profile"""
    try:
        auth_customer_id = request.user_id
        data = json.loads(request.body)
        
        with transaction.atomic():
            customer = Customer.objects.get(auth_customer_id=auth_customer_id)
            
            # Update fields if provided
            if 'full_name' in data:
                customer.full_name = data['full_name']
            
            if 'phone' in data:
                customer.phone = data['phone']
            
            if 'address' in data:
                customer.address = data['address']
            
            customer.save()
        
        return JsonResponse({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Profile updated successfully'
        })
    
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer profile not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@jwt_required(user_types=['customer'])
def list_addresses(request):
    """List all shipping addresses for current customer"""
    try:
        customer = Customer.objects.get(auth_customer_id=request.user_id)
        addresses = ShippingAddress.objects.filter(customer=customer).order_by('-is_default', '-created_at')
        return JsonResponse({
            'success': True,
            'data': [addr.to_dict() for addr in addresses]
        })
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def add_address(request):
    """Add a new shipping address"""
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name')
        phone = data.get('phone')
        address_line = data.get('address_line')
        is_default = data.get('is_default', False)
        
        if not full_name or not phone or not address_line:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
        customer = Customer.objects.get(auth_customer_id=request.user_id)
        
        # If this is default, unset other defaults
        if is_default:
            ShippingAddress.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        # If first address, make it default
        if not ShippingAddress.objects.filter(customer=customer).exists():
            is_default = True
            
        address = ShippingAddress.objects.create(
            customer=customer,
            full_name=full_name,
            phone=phone,
            address_line=address_line,
            is_default=is_default
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Address added successfully',
            'data': address.to_dict()
        }, status=201)
        
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['customer'])
def delete_address(request, address_id):
    """Delete a shipping address"""
    try:
        customer = Customer.objects.get(auth_customer_id=request.user_id)
        address = ShippingAddress.objects.get(id=address_id, customer=customer)
        
        was_default = address.is_default
        address.delete()
        
        # If we deleted the default, make another one default if available
        if was_default:
            next_addr = ShippingAddress.objects.filter(customer=customer).first()
            if next_addr:
                next_addr.is_default = True
                next_addr.save()
                
        return JsonResponse({
            'success': True,
            'message': 'Address deleted successfully'
        })
    except (Customer.DoesNotExist, ShippingAddress.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['customer'])
def set_default_address(request, address_id):
    """Set a shipping address as default"""
    try:
        customer = Customer.objects.get(auth_customer_id=request.user_id)
        
        # Unset current default
        ShippingAddress.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        # Set new default
        address = ShippingAddress.objects.get(id=address_id, customer=customer)
        address.is_default = True
        address.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Default address updated successfully',
            'data': address.to_dict()
        })
    except (Customer.DoesNotExist, ShippingAddress.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Address not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required(user_types=['staff'])
def get_customer_stats(request):
    """Get customer statistics (Staff only)"""
    total = Customer.objects.count()
    return JsonResponse({
        'success': True,
        'data': {
            'total_users': total
        }
    })
