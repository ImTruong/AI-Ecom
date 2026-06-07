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
from .application.use_cases import SupplierUseCases
from .domain.exceptions import SupplierValidationError
from .infrastructure.repositories import DjangoSupplierRepository
from .presentation.serializers import supplier_to_dict


supplier_use_cases = SupplierUseCases(DjangoSupplierRepository())

@require_http_methods(["GET"])
@jwt_required(user_types=['staff', 'admin'])
def list_suppliers(request):
    """List all active suppliers (Staff only)"""
    try:
        only_active = request.GET.get('only_active', 'false').lower() == 'true'
        search_query = request.GET.get('search')
        suppliers = supplier_use_cases.list_suppliers(only_active=only_active, search_query=search_query)
        
        return JsonResponse({
            'success': True,
            'data': [supplier_to_dict(s) for s in suppliers]
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
@jwt_required(user_types=['staff', 'admin'])
def get_supplier(request, supplier_id):
    """Get supplier details"""
    try:
        supplier = supplier_use_cases.get_supplier(supplier_id)
        return JsonResponse({
            'success': True,
            'data': supplier_to_dict(supplier)
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff', 'admin'])
def create_supplier(request):
    """Create a new supplier"""
    try:
        data = json.loads(request.body)
        supplier = supplier_use_cases.create_supplier(data)
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier created successfully',
            'data': supplier_to_dict(supplier)
        }, status=201)
    except SupplierValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
@jwt_required(user_types=['staff', 'admin'])
def update_supplier(request, supplier_id):
    """Update supplier info"""
    try:
        data = json.loads(request.body)
        supplier = supplier_use_cases.update_supplier(supplier_id, data)
        return JsonResponse({
            'success': True,
            'message': 'Supplier updated successfully',
            'data': supplier_to_dict(supplier)
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['staff', 'admin'])
def delete_supplier(request, supplier_id):
    """Delete a supplier"""
    try:
        supplier_use_cases.deactivate_supplier(supplier_id)
        return JsonResponse({
            'success': True,
            'message': 'Supplier deactivated successfully'
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
