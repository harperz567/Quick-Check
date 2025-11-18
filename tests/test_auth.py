import pytest
from auth.password_utils import hash_password, verify_password
from auth.auth_utils import generate_token, verify_token

class TestPasswordUtils:
    """Test password encryption utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = 'test123'
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith('$2b$')
    
    def test_verify_password_correct(self):
        """Test correct password verification"""
        password = 'test123'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """Test incorrect password verification"""
        password = 'test123'
        hashed = hash_password(password)
        
        assert verify_password('wrong_password', hashed) == False
    
    def test_different_passwords_different_hashes(self):
        """Test that same password produces different hashes due to salt"""
        password = 'test123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True

class TestAuthAPI:
    """Test authentication API endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'full_name': 'New User',
            'date_of_birth': '1995-01-01'
        })
        
        assert response.status_code == 201
        assert 'token' in response.json
        assert response.json['user']['username'] == 'newuser'
        assert response.json['user']['role'] == 'patient'
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        response = client.post('/api/auth/register', json={
            'username': 'test_patient',
            'email': 'new@test.com',
            'password': 'password123',
            'full_name': 'Test User',
            'date_of_birth': '1995-01-01'
        })
        
        assert response.status_code == 409
        assert 'already exists' in response.json['error']
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser2',
            'email': 'patient@test.com',
            'password': 'password123',
            'full_name': 'Test User',
            'date_of_birth': '1995-01-01'
        })
        
        assert response.status_code == 409
        assert 'already exists' in response.json['error']
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@test.com'
        })
        
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'username': 'test_patient',
            'password': 'test123'
        })
        
        assert response.status_code == 200
        assert 'token' in response.json
        assert 'user' in response.json
        assert response.json['user']['role'] == 'patient'
    
    def test_login_wrong_password(self, client):
        """Test login with incorrect password"""
        response = client.post('/api/auth/login', json={
            'username': 'test_patient',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['error']
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username"""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'test123'
        })
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['error']
    
    def test_login_missing_fields(self, client):
        """Test login with missing credentials"""
        response = client.post('/api/auth/login', json={
            'username': 'test_patient'
        })
        
        assert response.status_code == 400

class TestJWTToken:
    """Test JWT token functionality"""
    
    def test_generate_and_verify_token(self, app):
        """Test token generation and verification"""
        with app.app_context():
            token = generate_token(user_id=1, role='patient')
            
            assert token is not None
            assert len(token) > 0
            
            payload = verify_token(token)
            assert payload is not None
            assert payload['user_id'] == 1
            assert payload['role'] == 'patient'
            assert 'exp' in payload
            assert 'iat' in payload
    
    def test_verify_invalid_token(self, app):
        """Test verification of invalid token"""
        with app.app_context():
            payload = verify_token('invalid.token.string')
            assert payload is None
    
    def test_verify_malformed_token(self, app):
        """Test verification of malformed token"""
        with app.app_context():
            payload = verify_token('not-a-real-token')
            assert payload is None

class TestAuthenticatedEndpoints:
    """Test endpoints requiring authentication"""
    
    def test_get_current_user_success(self, client, patient_token):
        """Test getting current user info with valid token"""
        response = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 200
        assert 'username' in response.json
        assert response.json['role'] == 'patient'
    
    def test_get_current_user_no_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid.token'
        })
        
        assert response.status_code == 401