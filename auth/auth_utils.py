import jwt
from datetime import datetime, timedelta
from flask import current_app
from models import db, Session
import hashlib

def generate_token(user_id: int, role: str) -> str:
    """
    生成JWT token
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )
    
    # 保存token到sessions表
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = Session(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=payload['exp']
    )
    db.session.add(session)
    db.session.commit()
    
    return token

def verify_token(token: str) -> dict:
    """
    验证JWT token
    返回payload或None
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        
        # 检查token是否被撤销
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = Session.query.filter_by(
            token_hash=token_hash,
            is_revoked=False
        ).first()
        
        if not session:
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def revoke_token(token: str) -> bool:
    """
    撤销token（登出时使用）
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = Session.query.filter_by(token_hash=token_hash).first()
    
    if session:
        session.is_revoked = True
        db.session.commit()
        return True
    return False