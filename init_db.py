"""
数据库初始化脚本
运行: python init_db.py
"""
from app import app, db
from models import User, Patient, Insurance, Visit, AuditLog, Session
from auth.password_utils import hash_password
from datetime import datetime

def init_database():
    """初始化数据库并创建测试数据"""
    with app.app_context():
        # 删除所有表
        print("Dropping all tables...")
        db.drop_all()
        
        # 创建所有表
        print("Creating all tables...")
        db.create_all()
        
        # 创建测试用户
        print("Creating test users...")
        
        # 1. Staff用户
        staff_user = User(
            username='staff_admin',
            email='staff@hospital.com',
            password_hash=hash_password('staff123'),
            role='staff',
            is_active=True
        )
        db.session.add(staff_user)
        
        # 2. 测试患者用户
        patient_user = User(
            username='john_doe',
            email='john@example.com',
            password_hash=hash_password('patient123'),
            role='patient',
            is_active=True
        )
        db.session.add(patient_user)
        db.session.flush()
        
        # 创建患者信息
        patient = Patient(
            user_id=patient_user.id,
            full_name='John Doe',
            date_of_birth=datetime.strptime('1990-01-01', '%Y-%m-%d').date(),
            phone='123-456-7890',
            address='123 Main St, Boston, MA'
        )
        db.session.add(patient)
        
        db.session.commit()
        
        print("✅ Database initialized successfully!")
        print("\nTest accounts:")
        print("Staff: username='staff_admin', password='staff123'")
        print("Patient: username='john_doe', password='patient123'")

if __name__ == '__main__':
    init_database()