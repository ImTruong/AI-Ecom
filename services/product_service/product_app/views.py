from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import (
    Category, Product, Book, Clothes, Laptop, Phone, Tablet,
    Camera, Headphone, Watch, Shoe, Furniture,
    Attribute, AttributeValue, ProductVariant, ProductVariantOption
)
from .services import VariantValidationError, save_product_from_payload
from .application.use_cases import ProductUseCases
from .infrastructure.repositories import DjangoProductRepository
from .presentation.serializers import (
    attribute_to_dict,
    category_to_dict,
    product_to_dict,
    variant_stock_to_dict,
)
import json
import sys
import os

# Add shared to path
try:
    sys.path.insert(0, '/shared')
    from jwt_utils import jwt_required
except ImportError:
    # Fallback if shared is not available
    def jwt_required(*args, **kwargs):
        return lambda f: f

TYPE_MODEL_MAP = {
    'book': Book,
    'clothes': Clothes,
    'laptop': Laptop,
    'phone': Phone,
    'tablet': Tablet,
    'camera': Camera,
    'headphone': Headphone,
    'watch': Watch,
    'shoe': Shoe,
    'furniture': Furniture,
}


product_use_cases = ProductUseCases(DjangoProductRepository())

def product_list(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search')
    products = product_use_cases.list_products(category_slug=category_slug, search_query=search_query)
    return JsonResponse([product_to_dict(product) for product in products], safe=False)

def product_detail(request, pk):
    try:
        product = product_use_cases.get_product(pk)
        return JsonResponse(product_to_dict(product))
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

def category_list(request):
    categories = Category.objects.all()
    return JsonResponse([category_to_dict(category) for category in categories], safe=False)

@csrf_exempt
@jwt_required(user_types=['staff', 'admin'])
def manage_product(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        product = product_use_cases.save_product(data)
            
        return JsonResponse({'success': True, 'id': product.id})
    except VariantValidationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@jwt_required(user_types=['staff', 'admin'])
def delete_product_manage(request, pk):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        product_use_cases.delete_product(pk)
        return JsonResponse({'success': True})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def update_stock(request):
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = data.get('quantity')

        if variant_id is None or quantity is None:
            return JsonResponse({'success': False, 'error': 'variant_id and quantity required'}, status=400)

        variant = product_use_cases.update_stock(int(variant_id), int(quantity))
        return JsonResponse({'success': True, 'data': variant_stock_to_dict(variant)})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Variant not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== ATTRIBUTE MANAGEMENT APIs ====================

@require_http_methods(["GET"])
def list_attributes(request):
    """List all attributes with their values"""
    try:
        attributes = Attribute.objects.prefetch_related('values').all()
        return JsonResponse({'success': True, 'attributes': [attribute_to_dict(attr) for attr in attributes]})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff', 'admin'])
def create_attribute(request):
    """Create a new attribute"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Attribute name is required'}, status=400)
        
        attribute, created = Attribute.objects.get_or_create(name=name)
        
        return JsonResponse({
            'success': True,
            'message': 'Attribute created successfully',
            'attribute': {
                'id': attribute.id,
                'name': attribute.name,
                'slug': attribute.slug,
                'values': []
            }
        }, status=201 if created else 200)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['staff', 'admin'])
def delete_attribute(request, attribute_id):
    """Delete an attribute and all its values"""
    try:
        attribute = Attribute.objects.get(id=attribute_id)
        attribute.delete()
        return JsonResponse({'success': True, 'message': 'Attribute deleted successfully'})
    except Attribute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Attribute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required(user_types=['staff', 'admin'])
def create_attribute_value(request, attribute_id):
    """Create a new value for an attribute"""
    try:
        attribute = Attribute.objects.get(id=attribute_id)
        data = json.loads(request.body)
        value = data.get('value')
        
        if not value:
            return JsonResponse({'success': False, 'error': 'Value is required'}, status=400)
        
        attr_value, created = AttributeValue.objects.get_or_create(
            attribute=attribute,
            value=value
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Value created successfully',
            'value': {
                'id': attr_value.id,
                'value': attr_value.value,
                'slug': attr_value.slug
            }
        }, status=201 if created else 200)
    except Attribute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Attribute not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@jwt_required(user_types=['staff', 'admin'])
def delete_attribute_value(request, value_id):
    """Delete an attribute value"""
    try:
        value = AttributeValue.objects.get(id=value_id)
        value.delete()
        return JsonResponse({'success': True, 'message': 'Value deleted successfully'})
    except AttributeValue.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Value not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_product_required_attributes(request, product_id):
    """Get all attributes required for a product's variants"""
    try:
        product = Product.objects.get(id=product_id)
        
        # Get all attributes used by this product's variants
        variant_ids = product.variants.values_list('id', flat=True)
        used_attrs = Attribute.objects.filter(
            values__variant_options__variant_id__in=variant_ids
        ).distinct()
        
        return JsonResponse({
            'success': True,
            'product_id': product_id,
            'required_attributes': [
                {'id': a.id, 'name': a.name}
                for a in used_attrs
            ],
            'all_attributes': [
                {'id': a.id, 'name': a.name}
                for a in Attribute.objects.all()
            ]
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
