from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import (
    Category, Product, Book, Clothes, Laptop, Phone, Tablet,
    Camera, Headphone, Watch, Shoe, Furniture,
    Attribute, AttributeValue, ProductVariant, ProductVariantOption
)
from django.db import transaction
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

def product_list(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search')
    
    products = Product.objects.filter(is_active=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    if search_query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    return JsonResponse([p.to_dict() for p in products], safe=False)

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk, is_active=True)
        return JsonResponse(product.to_dict())
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

def category_list(request):
    categories = Category.objects.all()
    return JsonResponse([
        {'id': c.id, 'name': c.name, 'slug': c.slug, 'description': c.description, 'icon': c.icon} 
        for c in categories
    ], safe=False)

@csrf_exempt
@jwt_required(user_types=['staff', 'admin'])
def manage_product(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        pid = data.get('id')
        product_type = data.get('product_type', '').lower()
        variants_payload = data.get('variants', [])

        model_class = Product

        with transaction.atomic():
            if pid:
                product = model_class.objects.get(pk=pid)
            else:
                product = model_class()
            
            # Base fields
            product.name = data.get('name')
            product.description = data.get('description')
            product.price = data.get('price')
            product.category_id = data.get('category_id')
            supplier_id = data.get('supplier_id')
            if supplier_id in [None, '']:
                supplier_id = 1
            product.supplier_id = supplier_id
            product.image_url = data.get('image_url', '')
            product.product_type = product_type or 'generic'

            reserved_keys = {
                'id', 'name', 'description', 'price', 'category_id', 'supplier_id',
                'image_url', 'product_type', 'attributes', 'variants'
            }
            attributes = data.get('attributes')
            if not isinstance(attributes, dict):
                attributes = {k: v for k, v in data.items() if k not in reserved_keys}
            product.attributes = attributes
            
            product.save()

            # Handle variants
            if isinstance(variants_payload, list):
                # Delete existing variants
                product.variants.all().delete()
                for variant in variants_payload:
                    if not isinstance(variant, dict):
                        continue
                    variant_obj = ProductVariant.objects.create(
                        product=product,
                        name=variant.get('name') or product.name,
                        price_override=variant.get('price_override'),
                        stock=variant.get('stock', 0),
                        sku=variant.get('sku', ''),
                        options=variant.get('options', {}) if isinstance(variant.get('options'), dict) else {},
                    )

                    option_values = variant.get('option_values', [])
                    if not isinstance(option_values, list):
                        continue
                    for opt in option_values:
                        if not isinstance(opt, dict):
                            continue
                        attr_name = opt.get('attribute')
                        value = opt.get('value')
                        if not attr_name or value is None:
                            continue
                        attribute, _ = Attribute.objects.get_or_create(name=str(attr_name))
                        attr_value, _ = AttributeValue.objects.get_or_create(
                            attribute=attribute,
                            value=str(value)
                        )
                        ProductVariantOption.objects.get_or_create(
                            variant=variant_obj,
                            attribute_value=attr_value
                        )
            
        return JsonResponse({'success': True, 'id': product.id})
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
        product = Product.objects.get(pk=pk)
        product.delete()
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

        variant = ProductVariant.objects.get(id=int(variant_id))
        variant.stock = int(variant.stock) + int(quantity)
        if variant.stock < 0:
            variant.stock = 0
        variant.save()
        return JsonResponse({'success': True, 'data': {'variant_id': variant.id, 'stock': variant.stock}})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Variant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== ATTRIBUTE MANAGEMENT APIs ====================

@require_http_methods(["GET"])
def list_attributes(request):
    """List all attributes with their values"""
    try:
        attributes = Attribute.objects.prefetch_related('values').all()
        data = []
        for attr in attributes:
            data.append({
                'id': attr.id,
                'name': attr.name,
                'slug': attr.slug,
                'values': [
                    {'id': v.id, 'value': v.value, 'slug': v.slug}
                    for v in attr.values.all()
                ]
            })
        return JsonResponse({'success': True, 'attributes': data})
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
