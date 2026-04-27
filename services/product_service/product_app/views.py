from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Category, Product, Book, Clothes, Laptop, Phone, Tablet, 
    Camera, Headphone, Watch, Shoe, Furniture
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
                'image_url', 'product_type', 'attributes'
            }
            attributes = data.get('attributes')
            if not isinstance(attributes, dict):
                attributes = {k: v for k, v in data.items() if k not in reserved_keys}
            product.attributes = attributes
            
            product.save()
            
        return JsonResponse({'success': True, 'id': product.id})
    except Exception as e:
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
