from functools import wraps
from flask import g, jsonify

def check_permission(resource_type: str, action: str):
    """
    检查用户是否有权限执行操作
    
    Args:
        resource_type: 'patient', 'visit', 'insurance', 'user'
        action: 'view', 'create', 'update', 'delete'
    """
    role = g.user_role
    
    # 权限矩阵
    permissions = {
        'staff': {
            'patient': ['view', 'create', 'update'],
            'visit': ['view', 'create', 'update'],
            'insurance': ['view', 'update'],
            'user': ['view']
        },
        'patient': {
            'patient': ['view'],  # 只能查看自己
            'visit': ['view', 'create'],  # 只能查看和创建自己的
            'insurance': ['view', 'update'],  # 只能操作自己的
        }
    }
    
    if role not in permissions:
        return False
    
    if resource_type not in permissions[role]:
        return False
    
    return action in permissions[role][resource_type]

def require_permission(resource_type: str, action: str):
    """
    权限装饰器
    
    使用: @require_permission('patient', 'view')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(resource_type, action):
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator