from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, ProductVariant, Category
from django.db import transaction
import json
import sys
import os

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))
from jwt_utils import jwt_required

def product_list(request):
    product_type = request.GET.get('type')
    category_id = request.GET.get('category_id')
    category_name = request.GET.get('category') # For backward compatibility
    
    products = Product.objects.filter(is_active=True)
    if product_type:
        products = products.filter(product_type=product_type)
    if category_id:
        products = products.filter(category_obj_id=category_id)
    elif category_name:
        products = products.filter(category_obj__name=category_name)
    
    return JsonResponse([p.to_dict() for p in products], safe=False)

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk, is_active=True)
        return JsonResponse(product.to_dict())
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

def category_list(request):
    categories = Category.objects.all()
    return JsonResponse([{'id': c.id, 'name': c.name, 'description': c.description} for c in categories], safe=False)

@csrf_exempt
@jwt_required(user_types=['staff'])
def manage_product(request):
    """Create or update product with variants"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        pid = data.get('id')
        
        with transaction.atomic():
            if pid:
                product = Product.objects.get(pk=pid)
            else:
                product = Product()
            
            product.name = data.get('name')
            product.description = data.get('description')
            product.price = data.get('price')
            product.product_type = data.get('product_type')
            product.category_obj_id = data.get('category_id') or None
            product.supplier_id = data.get('supplier_id') or None
            product.image_url = data.get('image_url', '')
            product.attributes = data.get('attributes', {})
            product.save()
            
            # Save variants
            if 'variants' in data:
                # For simplicity in this refactor, we replace variants 
                # or you could sync them. Let's sync.
                existing_variants = {v.id: v for v in product.variants.all()}
                new_variants_data = data.get('variants', [])
                
                # Clear all for now to avoid complexity of matching
                product.variants.all().delete()
                
                for v_data in new_variants_data:
                    ProductVariant.objects.create(
                        product=product,
                        name=v_data.get('name'),
                        price_override=v_data.get('price_override'),
                        stock=v_data.get('stock', 0),
                        sku=v_data.get('sku'),
                        options=v_data.get('options', {}) # Can be extended later
                    )
        
        return JsonResponse({'success': True, 'id': product.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@jwt_required(user_types=['staff'])
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
def get_variant_stock(request, variant_id):
    try:
        variant = ProductVariant.objects.get(pk=variant_id)
        return JsonResponse({'id': variant.id, 'stock': variant.stock})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'Variant not found'}, status=404)

@csrf_exempt
def update_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            variant_id = data.get('variant_id')
            quantity = data.get('quantity') # positive to add, negative to subtract
            
            variant = ProductVariant.objects.get(pk=variant_id)
            variant.stock += quantity
            variant.save()
            return JsonResponse({'status': 'success', 'new_stock': variant.stock})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
