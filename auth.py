import jwt
from functools import wraps
from flask import request, jsonify, current_app
from models import User, db
from datetime import datetime, timedelta

def generate_token(user_id, role):
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = User.query.get(payload['user_id'])
        if not user or user.status != 'active':
            return jsonify({'error': 'User not found or inactive'}), 401
        
        request.current_user = user
        request.current_user_role = user.role
        return f(*args, **kwargs)
    return decorated

def roles_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user_role not in allowed_roles:
                return jsonify({'error': f'Permission denied. Required roles: {allowed_roles}'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
