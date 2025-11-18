import pytest
from security.encryption import encrypt_data, decrypt_data
from security.rbac import check_permission
from flask import g

class TestEncryption:
    """Test data encryption functionality"""
    
    def test_encrypt_decrypt_ssn(self, app):
        """Test encrypting and decrypting SSN"""
        with app.app_context():
            ssn = '123-45-6789'
            
            encrypted = encrypt_data(ssn)
            assert encrypted != ssn
            assert len(encrypted) > 0
            
            decrypted = decrypt_data(encrypted)
            assert decrypted == ssn
    
    def test_encrypt_decrypt_insurance_id(self, app):
        """Test encrypting and decrypting insurance ID"""
        with app.app_context():
            insurance_id = 'INS123456789'
            
            encrypted = encrypt_data(insurance_id)
            assert encrypted != insurance_id
            
            decrypted = decrypt_data(encrypted)
            assert decrypted == insurance_id
    
    def test_encrypt_none(self, app):
        """Test encrypting None value"""
        with app.app_context():
            result = encrypt_data(None)
            assert result is None
    
    def test_decrypt_none(self, app):
        """Test decrypting None value"""
        with app.app_context():
            result = decrypt_data(None)
            assert result is None
    
    def test_encryption_produces_different_output(self, app):
        """Test that same data encrypted twice produces different ciphertext"""
        with app.app_context():
            data = 'sensitive-data'
            
            encrypted1 = encrypt_data(data)
            encrypted2 = encrypt_data(data)
            
            # Different ciphertext due to encryption
            # But both should decrypt to same value
            assert decrypt_data(encrypted1) == data
            assert decrypt_data(encrypted2) == data

class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_staff_can_view_patients(self, app):
        """Test staff permission to view patients"""
        with app.app_context():
            with app.test_request_context():
                g.user_role = 'staff'
                assert check_permission('patient', 'view') == True
    
    def test_staff_can_create_patients(self, app):
        """Test staff permission to create patient records"""
        with app.app_context():
            with app.test_request_context():
                g.user_role = 'staff'
                assert check_permission('patient', 'create') == True
    
    def test_patient_can_view_own_data(self, app):
        """Test patient permission to view their own data"""
        with app.app_context():
            with app.test_request_context():
                g.user_role = 'patient'
                assert check_permission('patient', 'view') == True
    
    def test_patient_cannot_delete(self, app):
        """Test patient cannot delete records"""
        with app.app_context():
            with app.test_request_context():
                g.user_role = 'patient'
                assert check_permission('patient', 'delete') == False
    
    def test_patient_can_create_visit(self, app):
        """Test patient can create visit records"""
        with app.app_context():
            with app.test_request_context():
                g.user_role = 'patient'
                assert check_permission('visit', 'create') == True

class TestAuditLog:
    """Test audit logging functionality"""
    
    def test_login_creates_audit_log(self, client, app):
        """Test that login action creates audit log entry"""
        from models import AuditLog
        
        response = client.post('/api/auth/login', json={
            'username': 'test_patient',
            'password': 'test123'
        })
        
        assert response.status_code == 200
        
        with app.app_context():
            logs = AuditLog.query.filter_by(
                action='login',
                resource_type='user'
            ).all()
            assert len(logs) > 0
            
            latest_log = logs[-1]
            assert latest_log.ip_address is not None
            assert latest_log.timestamp is not None
    
    def test_audit_log_records_user_agent(self, client, app):
        """Test that audit log captures user agent"""
        from models import AuditLog
        
        client.post('/api/auth/login', 
                   json={'username': 'test_patient', 'password': 'test123'},
                   headers={'User-Agent': 'TestAgent/1.0'})
        
        with app.app_context():
            log = AuditLog.query.filter_by(action='login').first()
            assert log.user_agent is not None

class TestSessionManagement:
    """Test session token management"""
    
    def test_login_creates_session_record(self, client, app):
        """Test that login creates session record in database"""
        from models import Session as SessionModel
        
        response = client.post('/api/auth/login', json={
            'username': 'test_patient',
            'password': 'test123'
        })
        
        assert response.status_code == 200
        
        with app.app_context():
            sessions = SessionModel.query.filter_by(is_revoked=False).all()
            assert len(sessions) > 0
    
    def test_logout_revokes_session(self, client, app, patient_token):
        """Test that logout revokes the session token"""
        from models import Session as SessionModel
        
        response = client.post('/api/auth/logout', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 200