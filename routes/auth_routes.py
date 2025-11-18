from flask import request, jsonify, render_template
from routes import auth_bp
from models import db, User, Patient
from auth.password_utils import hash_password, verify_password
from auth.auth_utils import generate_token, revoke_token
from security.audit import log_action
from datetime import datetime

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    
    Body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "secure_password",
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "phone": "123-456-7890",
        "role": "patient"  // 可选，默认patient
    }
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'email', 'password', 'full_name', 'date_of_birth']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # 检查用户是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        # 创建用户
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hash_password(data['password']),
            role=data.get('role', 'patient'),  # 默认角色为patient
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()  # 获取user.id
        
        # 如果是患者，创建患者记录
        if user.role == 'patient':
            patient = Patient(
                user_id=user.id,
                full_name=data['full_name'],
                date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
                phone=data.get('phone'),
                address=data.get('address')
            )
            db.session.add(patient)
        
        db.session.commit()
        
        # 生成JWT token
        token = generate_token(user.id, user.role)
        
        # 记录审计日志
        log_action('create', 'user', user.id, {'username': user.username})
        
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    
    Body:
    {
        "username": "john_doe",
        "password": "secure_password"
    }
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # 验证密码
        if not verify_password(data['password'], user.password_hash):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # 检查账户是否激活
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 生成JWT token
        token = generate_token(user.id, user.role)
        
        # 记录审计日志
        log_action('login', 'user', user.id, {'username': user.username})
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出（撤销token）
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token required'}), 401
        
        # 撤销token
        if revoke_token(token):
            return jsonify({'message': 'Logout successful'}), 200
        else:
            return jsonify({'error': 'Invalid token'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    获取当前登录用户信息
    
    Headers:
        Authorization: Bearer <token>
    """
    from auth.decorators import require_auth
    from flask import g
    
    @require_auth
    def _get_user():
        user = g.current_user
        
        response = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        }
        
        # 如果是患者，返回患者信息
        if user.role == 'patient' and user.patient:
            response['patient'] = {
                'full_name': user.patient.full_name,
                'date_of_birth': user.patient.date_of_birth.isoformat(),
                'phone': user.patient.phone
            }
        
        return jsonify(response), 200
    
    return _get_user()