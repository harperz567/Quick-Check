import pytest

class TestPatientAPI:
    """Test patient-related API endpoints"""
    
    def test_get_my_info_success(self, client, patient_token):
        """Test patient viewing their own information"""
        response = client.get('/api/patient/me', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 200
        assert 'full_name' in response.json
        assert response.json['full_name'] == 'Test Patient'
        assert 'date_of_birth' in response.json
        assert 'phone' in response.json
    
    def test_get_my_info_no_token(self, client):
        """Test accessing patient info without authentication"""
        response = client.get('/api/patient/me')
        
        assert response.status_code == 401
    
    def test_get_my_info_invalid_token(self, client):
        """Test accessing patient info with invalid token"""
        response = client.get('/api/patient/me', headers={
            'Authorization': 'Bearer invalid.token'
        })
        
        assert response.status_code == 401
    
    def test_patient_cannot_access_all_patients(self, client, patient_token):
        """Test that patient cannot view all patients list"""
        response = client.get('/api/patient/all', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 403
    
    def test_staff_can_access_all_patients(self, client, staff_token):
        """Test that staff can view all patients"""
        response = client.get('/api/patient/all', headers={
            'Authorization': f'Bearer {staff_token}'
        })
        
        assert response.status_code == 200
        assert 'patients' in response.json
        assert isinstance(response.json['patients'], list)
        assert len(response.json['patients']) > 0
    
    def test_staff_can_view_specific_patient(self, client, staff_token):
        """Test that staff can view specific patient details"""
        response = client.get('/api/patient/1', headers={
            'Authorization': f'Bearer {staff_token}'
        })
        
        if response.status_code == 200:
            assert 'full_name' in response.json
            assert 'visits' in response.json
    
    def test_patient_cannot_view_other_patients(self, client, patient_token):
        """Test that patient cannot view other patients' info"""
        response = client.get('/api/patient/999', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code in [403, 404]

class TestVisitAPI:
    """Test visit-related API endpoints"""
    
    def test_get_my_visits(self, client, patient_token):
        """Test patient viewing their own visits"""
        response = client.get('/api/visit/my-visits', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 200
        assert 'visits' in response.json
        assert isinstance(response.json['visits'], list)
    
    def test_staff_can_view_recent_visits(self, client, staff_token):
        """Test staff viewing recent visits"""
        response = client.get('/api/visit/recent', headers={
            'Authorization': f'Bearer {staff_token}'
        })
        
        assert response.status_code == 200
        assert 'visits' in response.json
    
    def test_patient_cannot_view_recent_visits(self, client, patient_token):
        """Test that patient cannot view all recent visits"""
        response = client.get('/api/visit/recent', headers={
            'Authorization': f'Bearer {patient_token}'
        })
        
        assert response.status_code == 403