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

from .models import Customer, Staff, RefreshToken


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
        
        return JsonResponse({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': customer.to_dict()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def staff_login(request):
    """Staff login"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password required'}, status=400)
        
        # Find staff
        try:
            staff = Staff.objects.get(email=email, is_active=True)
        except Staff.DoesNotExist:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Check password
        if not staff.check_password(password):
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate tokens
        access_token = jwt_manager.generate_access_token(
            user_id=staff.id,
            user_type='staff',
            email=staff.email,
            expires_in=settings.JWT_ACCESS_TOKEN_LIFETIME
        )
        
        refresh_token = jwt_manager.generate_refresh_token(
            user_id=staff.id,
            user_type='staff',
            expires_in=settings.JWT_REFRESH_TOKEN_LIFETIME
        )
        
        # Save refresh token
        RefreshToken.objects.create(
            token=refresh_token,
            user_type='staff',
            user_id=staff.id,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': staff.to_dict()
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
