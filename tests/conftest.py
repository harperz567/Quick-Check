import pytest
from app import app as flask_app
from models import db, User, Patient
from auth.password_utils import hash_password
from datetime import datetime

@pytest.fixture
def app():
    """Create test Flask application"""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://harper@localhost:5432/healthcare_test_db',
        'JWT_SECRET_KEY': 'test-secret-key-for-testing',
        'ENCRYPTION_KEY': 'test-encryption-key-32bytes!!',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with flask_app.app_context():
        db.create_all()
        
        # Create test patient user
        test_patient = User(
            username='test_patient',
            email='patient@test.com',
            password_hash=hash_password('test123'),
            role='patient',
            is_active=True
        )
        db.session.add(test_patient)
        db.session.flush()
        
        # Create patient profile
        test_patient_info = Patient(
            user_id=test_patient.id,
            full_name='Test Patient',
            date_of_birth=datetime.strptime('1990-01-01', '%Y-%m-%d').date(),
            phone='123-456-7890'
        )
        db.session.add(test_patient_info)
        
        # Create test staff user
        test_staff = User(
            username='test_staff',
            email='staff@test.com',
            password_hash=hash_password('staff123'),
            role='staff',
            is_active=True
        )
        db.session.add(test_staff)
        
        db.session.commit()
        
        yield flask_app
        
        # Cleanup
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def patient_token(client):
    """Get patient authentication token"""
    response = client.post('/api/auth/login', json={
        'username': 'test_patient',
        'password': 'test123'
    })
    return response.json['token']

@pytest.fixture
def staff_token(client):
    """Get staff authentication token"""
    response = client.post('/api/auth/login', json={
        'username': 'test_staff',
        'password': 'staff123'
    })
    return response.json['token']