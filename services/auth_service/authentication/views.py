"""
Authentication views
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.conf import settings
import json
import sys
import os
from datetime import datetime, timedelta

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from jwt_utils import JWTManager
from outbox.service import create_outbox_event_and_save
from events import EventType

from .models import Customer, Staff, RefreshToken, Admin, Role, Permission, StaffRole, Address


jwt_manager = JWTManager(settings.JWT_SECRET_KEY)


@csrf_exempt
@require_http_methods(["POST"])
def customer_register(request):
    """Register a new customer"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        phone = data.get('phone', '')
        address = data.get('address', '')
        
        # Validation
        if not email or not password or not full_name:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Check if customer already exists
        if Customer.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)
        
        # Create customer with transaction
        with transaction.atomic():
            customer = Customer(
                email=email,
                full_name=full_name,
                phone=phone,
                address=address
            )
            customer.set_password(password)
            customer.save()
            
            # Create event in outbox
            create_outbox_event_and_save(
                event_type=EventType.CUSTOMER_REGISTERED,
                aggregate_id=str(customer.id),
                data={
                    'customer_id': customer.id,
                    'user_id': customer.id,
                    'id': customer.id,
                    'email': customer.email,
                    'full_name': customer.full_name,
                    'phone': customer.phone,
                    'address': customer.address,
                }
            )
        
        # Generate tokens for immediate login after registration
        access_token = jwt_manager.generate_access_token(
            user_id=customer.id,
            user_type='customer',
            email=customer.email,
            expires_in=settings.JWT_ACCESS_TOKEN_LIFETIME
        )
        refresh_token = jwt_manager.generate_refresh_token(
            user_id=customer.id,
            user_type='customer',
            expires_in=settings.JWT_REFRESH_TOKEN_LIFETIME
        )
        
        # Save refresh token
        RefreshToken.objects.create(
            token=refresh_token,
            user_type='customer',
            user_id=customer.id,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Customer registered successfully',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': customer.to_dict()
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def customer_login(request):
    """Customer login"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)
        
        # Find customer
        try:
            customer = Customer.objects.get(email=email, is_active=True)
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Check password
        if not customer.check_password(password):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate tokens
        access_token = jwt_manager.generate_access_token(
            user_id=customer.id,
            user_type='customer',
            email=customer.email,
            expires_in=settings.JWT_ACCESS_TOKEN_LIFETIME
        )
        
        refresh_token = jwt_manager.generate_refresh_token(
            user_id=customer.id,
            user_type='customer',
            expires_in=settings.JWT_REFRESH_TOKEN_LIFETIME
        )
        
        # Save refresh token
        RefreshToken.objects.create(
            token=refresh_token,
            user_type='customer',
            user_id=customer.id,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        )
        
        # Add role to user dict
        user_data = customer.to_dict()
        user_data['role'] = 'customer'
        
        return JsonResponse({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_data
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def staff_login(request):
    """Staff/Admin login"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)
        
        # Check if it's an admin first
        try:
            admin = Admin.objects.get(email=email, is_active=True)
            user = admin
            user_type = 'admin'
            is_admin = True
        except Admin.DoesNotExist:
            # Not an admin, try regular staff
            try:
                staff = Staff.objects.get(email=email, is_active=True)
                user = staff
                user_type = 'staff'
                is_admin = False
            except Staff.DoesNotExist:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Check password
        if not user.check_password(password):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate tokens
        access_token = jwt_manager.generate_access_token(
            user_id=user.id,
            user_type=user_type,
            email=user.email,
            expires_in=settings.JWT_ACCESS_TOKEN_LIFETIME
        )
        
        refresh_token = jwt_manager.generate_refresh_token(
            user_id=user.id,
            user_type=user_type,
            expires_in=settings.JWT_REFRESH_TOKEN_LIFETIME
        )
        
        # Save refresh token
        RefreshToken.objects.create(
            token=refresh_token,
            user_type=user_type,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        )
        
        # Build user dict with role
        user_data = user.to_dict()
        user_data['role'] = user_type
        if is_admin:
            user_data['admin_level'] = user.admin_level
        
        return JsonResponse({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_data
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def token_refresh(request):
    """Refresh access token using refresh token"""
    try:
        data = json.loads(request.body)
        refresh_token_str = data.get('refresh_token')
        
        if not refresh_token_str:
            return JsonResponse({'error': 'Refresh token required'}, status=400)
        
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_token_str, 'refresh')
        if not payload:
            return JsonResponse({'error': 'Invalid refresh token'}, status=401)
        
        # Check if token exists and is valid
        try:
            refresh_token = RefreshToken.objects.get(token=refresh_token_str)
            if not refresh_token.is_valid():
                return JsonResponse({'error': 'Refresh token expired or revoked'}, status=401)
        except RefreshToken.DoesNotExist:
            return JsonResponse({'error': 'Invalid refresh token'}, status=401)
        
        # Generate new access token
        access_token = jwt_manager.generate_access_token(
            user_id=payload['user_id'],
            user_type=payload['user_type'],
            email=payload.get('email', ''),
            expires_in=settings.JWT_ACCESS_TOKEN_LIFETIME
        )
        
        return JsonResponse({
            'access_token': access_token
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def token_verify(request):
    """Verify if a token is valid"""
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'Token required'}, status=400)
        
        payload = jwt_manager.verify_token(token, 'access')
        
        if payload:
            return JsonResponse({
                'valid': True,
                'user_id': payload.get('user_id'),
                'user_type': payload.get('user_type'),
                'email': payload.get('email')
            })
        else:
            return JsonResponse({'valid': False}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== ADMIN USER MANAGEMENT APIs ====================

def require_admin(view_func):
    """Decorator to require admin authentication"""
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        token = auth_header.split(' ')[1]
        payload = jwt_manager.verify_token(token, 'access')
        
        if not payload:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        if payload.get('user_type') != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        
        request.user_payload = payload
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_http_methods(["GET"])
@require_admin
def admin_list_users(request):
    """List all users (customers and staff) - Admin only"""
    try:
        user_type = request.GET.get('type', 'all')  # 'customer', 'staff', 'admin', 'all'
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', 'all')  # 'active', 'inactive', 'all'
        
        users = []
        
        # Get customers
        if user_type in ['all', 'customer']:
            customers = Customer.objects.all()
            if search:
                customers = customers.filter(email__icontains=search) | \
                           customers.filter(full_name__icontains=search)
            if status_filter != 'all':
                is_active = status_filter == 'active'
                customers = customers.filter(is_active=is_active)
            
            for c in customers:
                user_data = c.to_dict()
                user_data['type'] = 'customer'
                user_data['address_count'] = c.addresses.filter(is_active=True).count()
                users.append(user_data)
        
        # Get staff
        if user_type in ['all', 'staff']:
            staff_list = Staff.objects.all()
            if search:
                staff_list = staff_list.filter(email__icontains=search) | \
                            staff_list.filter(full_name__icontains=search)
            if status_filter != 'all':
                is_active = status_filter == 'active'
                staff_list = staff_list.filter(is_active=is_active)
            
            for s in staff_list:
                user_data = s.to_dict()
                user_data['type'] = 'staff'
                user_data['roles'] = [sr.role.name for sr in s.staff_roles.all()]
                users.append(user_data)
        
        # Get admins
        if user_type in ['all', 'admin']:
            admins = Admin.objects.all()
            if search:
                admins = admins.filter(email__icontains=search) | \
                        admins.filter(full_name__icontains=search)
            if status_filter != 'all':
                is_active = status_filter == 'active'
                admins = admins.filter(is_active=is_active)
            
            for a in admins:
                user_data = a.to_dict()
                users.append(user_data)
        
        return JsonResponse({
            'success': True,
            'users': users,
            'total': len(users)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_admin
def admin_get_user(request, user_id):
    """Get user details - Admin only"""
    try:
        user_type = request.GET.get('type', 'customer')
        
        if user_type == 'customer':
            user = Customer.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            user_data = user.to_dict()
            user_data['type'] = 'customer'
            user_data['addresses'] = [a.to_dict() for a in user.addresses.filter(is_active=True)]
            
        elif user_type == 'staff':
            user = Staff.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            user_data = user.to_dict()
            user_data['type'] = 'staff'
            user_data['roles'] = [
                {'id': sr.role.id, 'name': sr.role.name} 
                for sr in user.staff_roles.all()
            ]
            
        elif user_type == 'admin':
            user = Admin.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            user_data = user.to_dict()
            
        else:
            return JsonResponse({'error': 'Invalid user type'}, status=400)
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@require_admin
def admin_create_staff(request):
    """Create new staff user - Admin only"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        phone = data.get('phone', '')
        role_names = data.get('roles', ['staff'])  # List of role names
        
        if not email or not password or not full_name:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        if Staff.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        
        with transaction.atomic():
            staff = Staff(
                email=email,
                full_name=full_name,
                phone=phone,
                role='staff',
                is_active=True
            )
            staff.set_password(password)
            staff.save()
            
            # Assign roles
            assigned_roles = []
            for role_name in role_names:
                try:
                    role = Role.objects.get(name=role_name)
                    StaffRole.objects.create(
                        staff=staff,
                        role=role,
                        assigned_by_id=request.user_payload.get('user_id')
                    )
                    assigned_roles.append(role_name)
                except Role.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'message': 'Staff user created successfully',
                'staff': {
                    'id': staff.id,
                    'email': staff.email,
                    'full_name': staff.full_name,
                    'roles': assigned_roles
                }
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
@require_admin
def admin_update_user(request, user_id):
    """Update user - Admin only"""
    try:
        data = json.loads(request.body)
        user_type = data.get('user_type', 'customer')
        
        if user_type == 'customer':
            user = Customer.objects.filter(id=user_id).first()
        elif user_type == 'staff':
            user = Staff.objects.filter(id=user_id).first()
        else:
            return JsonResponse({'error': 'Invalid user type'}, status=400)
        
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Update fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_admin
def admin_delete_user(request, user_id):
    """Soft delete user (deactivate) - Admin only"""
    try:
        user_type = request.GET.get('type', 'customer')
        
        if user_type == 'customer':
            user = Customer.objects.filter(id=user_id).first()
        elif user_type == 'staff':
            user = Staff.objects.filter(id=user_id).first()
        else:
            return JsonResponse({'error': 'Invalid user type'}, status=400)
        
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Soft delete (deactivate)
        user.is_active = False
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User deactivated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== ROLE MANAGEMENT APIs ====================

@csrf_exempt
@require_http_methods(["GET"])
@require_admin
def admin_list_roles(request):
    """List all roles - Admin only"""
    try:
        roles = Role.objects.filter(is_active=True)
        return JsonResponse({
            'success': True,
            'roles': [role.to_dict() for role in roles]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_admin
def admin_list_permissions(request):
    """List all permissions - Admin only"""
    try:
        perms = Permission.objects.all()
        return JsonResponse({
            'success': True,
            'permissions': [
                {'id': p.id, 'name': p.name, 'codename': p.codename} 
                for p in perms
            ]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
