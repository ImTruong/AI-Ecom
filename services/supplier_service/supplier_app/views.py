from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import sys
import os

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from jwt_utils import jwt_required
from .models import Supplier

@require_http_methods(["GET"])
def list_suppliers(request):
    """List all active suppliers (Staff only)"""
    try:
        only_active = request.GET.get('only_active', 'false').lower() == 'true'
        if only_active:
            suppliers = Supplier.objects.filter(is_active=True)
        else:
            suppliers = Supplier.objects.all()
        
        return JsonResponse({
            'success': True,
            'data': [s.to_dict() for s in suppliers]
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@jwt_required(user_types=['staff'])
def get_supplier(request, supplier_id):
    """Get supplier details"""
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        return JsonResponse({
            'success': True,
            'data': supplier.to_dict()
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff'])
def create_supplier(request):
    """Create a new supplier"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address')
        
        if not name or not email or not phone or not address:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
        supplier = Supplier.objects.create(
            name=name,
            contact_name=data.get('contact_name', ''),
            email=email,
            phone=phone,
            address=address
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier created successfully',
            'data': supplier.to_dict()
        }, status=201)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
@jwt_required(user_types=['staff'])
def update_supplier(request, supplier_id):
    """Update supplier info"""
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        data = json.loads(request.body)
        
        fields = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active']
        for field in fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.save()
        return JsonResponse({
            'success': True,
            'message': 'Supplier updated successfully',
            'data': supplier.to_dict()
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['staff'])
def delete_supplier(request, supplier_id):
    """Delete a supplier"""
    try:
        supplier = Supplier.objects.get(id=supplier_id)
        # Maybe do a soft delete?
        supplier.is_active = False
        supplier.save()
        # supplier.delete() # Or hard delete
        return JsonResponse({
            'success': True,
            'message': 'Supplier deactivated successfully'
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
