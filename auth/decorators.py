from functools import wraps
from flask import request, jsonify, g
from auth.auth_utils import verify_token
from models import User

# ============ 第1个：用于API的装饰器（保留原来的）============
def require_auth(f):
    """
    用于API的认证装饰器
    检查HTTP Header里的JWT token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # 从Header获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer TOKEN"
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # 获取用户信息
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # 将用户信息存储到g对象中
        g.current_user = user
        g.user_id = user.id
        g.user_role = user.role
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============ 第2个：用于HTML页面的装饰器（新增）============
def require_auth_page(f):
    """
    用于HTML页面的装饰器
    不检查token，让前端JavaScript去检查
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 直接放行，认证由前端JS完成
        return f(*args, **kwargs)
    
    return decorated_function


# ============ 第3个：角色检查装饰器（保留原来的）============
def require_role(*roles):
    """
    要求特定角色的装饰器
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user_role'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if g.user_role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator