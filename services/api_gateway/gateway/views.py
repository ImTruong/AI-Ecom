"""
Gateway views for frontend pages
"""
from django.shortcuts import render
from django.http import JsonResponse


def homepage(request):
    """Homepage with product grid"""
    return render(request, 'homepage.html')


def cart_page(request):
    """Shopping cart page"""
    return render(request, 'cart.html')


def profile_page(request):
    """Customer profile page"""
    return render(request, 'profile.html')


def login_page(request):
    """Login page"""
    return render(request, 'login.html')


def register_page(request):
    """Registration page"""
    return render(request, 'register.html')

def checkout_page(request):
    """Checkout page"""
    return render(request, 'checkout.html')

def orders_page(request):
    """Order history page"""
    return render(request, 'orders.html')


def staff_login_page(request):
    """Staff Login page"""
    return render(request, 'staff_login.html')


def staff_dashboard(request):
    """Staff Dashboard page"""
    return render(request, 'staff_dashboard.html')


def staff_orders(request):
    """Staff Order management page"""
    return render(request, 'staff_orders.html')

def staff_products(request):
    """Staff Product management page"""
    return render(request, 'staff_products.html')

def staff_suppliers(request):
    """Staff Supplier management page"""
    return render(request, 'staff_suppliers.html')

def staff_users(request):
    """Staff User management page"""
    return render(request, 'staff_users.html')

def staff_knowledge(request):
    """Staff Knowledge Base management page"""
    return render(request, 'staff_knowledge.html')

def product_detail(request, product_id):
    """Product detail page"""
    return render(request, 'product_detail.html', {
        'product_id': product_id
    })

def search_page(request):
    """Search results page"""
    query = request.GET.get('q', '')
    return render(request, 'search.html', {'query': query})

def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'api_gateway'
    })
