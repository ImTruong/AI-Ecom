"""
Shared JWT utilities for microservices
"""
import jwt
import datetime
from typing import Dict, Optional
from functools import wraps
from django.http import JsonResponse


class JWTManager:
    """JWT token management"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_access_token(self, user_id: int, user_type: str, email: str, 
                             expires_in: int = 3600) -> str:
        """
        Generate JWT access token
        
        Args:
            user_id: User ID
            user_type: 'customer' or 'staff'
            email: User email
            expires_in: Token expiration in seconds (default 1 hour)
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user_id: int, user_type: str, 
                               expires_in: int = 86400) -> str:
        """
        Generate JWT refresh token
        
        Args:
            user_id: User ID
            user_type: 'customer' or 'staff'
            expires_in: Token expiration in seconds (default 24 hours)
        
        Returns:
            JWT refresh token string
        """
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
            'iat': datetime.datetime.utcnow(),
            'type': 'refresh'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decode and validate JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """
        Verify token and check token type
        
        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
        
        Returns:
            Decoded payload or None if invalid
        """
        payload = self.decode_token(token)
        if payload and payload.get('type') == token_type:
            return payload
        return None


def jwt_required(user_types: list = None):
    """
    Decorator to require JWT authentication
    
    Args:
        user_types: List of allowed user types ['customer', 'staff']. None allows all.
    
    Usage:
        @jwt_required(user_types=['customer'])
        def my_view(request):
            user_id = request.user_id
            user_type = request.user_type
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Missing or invalid authorization header'}, status=401)
            
            token = auth_header.split(' ')[1]
            
            # Get JWT secret from settings
            from django.conf import settings
            secret = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            jwt_manager = JWTManager(secret)
            
            payload = jwt_manager.verify_token(token, 'access')
            
            if not payload:
                return JsonResponse({'error': 'Invalid or expired token'}, status=401)
            
            # Check user type if specified
            if user_types and payload.get('user_type') not in user_types:
                return JsonResponse({'error': 'Unauthorized user type'}, status=403)
            
            # Attach user info to request
            request.user_id = payload.get('user_id')
            request.user_type = payload.get('user_type')
            request.user_email = payload.get('email')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def extract_token_from_request(request) -> Optional[str]:
    """Extract JWT token from request header"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None
