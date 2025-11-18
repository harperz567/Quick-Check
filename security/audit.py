from flask import request, g
from models import db, AuditLog
from datetime import datetime

def log_action(action: str, resource_type: str, resource_id: int = None, details: dict = None):
    """
    记录审计日志
    
    Args:
        action: 'view', 'create', 'update', 'delete'
        resource_type: 'patient', 'visit', 'insurance', 'user'
        resource_id: 资源ID
        details: 额外信息（dict）
    """
    user_id = getattr(g, 'user_id', None)
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        timestamp=datetime.utcnow(),
        details=details
    )
    
    db.session.add(audit_log)
    db.session.commit()
    
    print(f"[AUDIT] User {user_id} performed {action} on {resource_type} {resource_id}")

def audit_decorator(action: str, resource_type: str):
    """
    审计装饰器
    使用: @audit_decorator('view', 'patient')
    """
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行函数
            result = f(*args, **kwargs)
            
            # 记录日志
            resource_id = kwargs.get('id') or kwargs.get('patient_id')
            log_action(action, resource_type, resource_id)
            
            return result
        
        return decorated_function
    return decorator