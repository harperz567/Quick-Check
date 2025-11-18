from flask import request, jsonify, g
from routes import patient_bp
from models import db, Patient, User, Visit, Insurance
from auth.decorators import require_auth, require_role
from security.audit import log_action, audit_decorator
from security.encryption import decrypt_data

@patient_bp.route('/all', methods=['GET'])
@require_auth
@require_role('staff')
@audit_decorator('view', 'patient_list')
def get_all_patients():
    """
    获取所有患者列表 - 仅staff可访问
    """
    try:
        patients = Patient.query.all()
        
        result = []
        for patient in patients:
            # 获取最后一次就诊时间
            last_visit = Visit.query.filter_by(patient_id=patient.id)\
                .order_by(Visit.visit_date.desc()).first()
            
            result.append({
                'id': patient.id,
                'full_name': patient.full_name,
                'date_of_birth': patient.date_of_birth.isoformat(),
                'phone': patient.phone,
                'last_visit': last_visit.visit_date.isoformat() if last_visit else None
            })
        
        return jsonify({'patients': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_bp.route('/<int:patient_id>', methods=['GET'])
@require_auth
def get_patient(patient_id):
    """
    获取患者详情
    - 患者只能查看自己
    - Staff可以查看所有
    """
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # 权限检查
        if g.user_role == 'patient' and patient.user_id != g.user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # 获取就诊记录
        visits = Visit.query.filter_by(patient_id=patient.id)\
            .order_by(Visit.visit_date.desc()).all()
        
        # 获取保险信息
        insurance = Insurance.query.filter_by(patient_id=patient.id).first()
        
        result = {
            'id': patient.id,
            'full_name': patient.full_name,
            'date_of_birth': patient.date_of_birth.isoformat(),
            'phone': patient.phone,
            'address': patient.address,
            'email': patient.user.email,
            'visits': [
                {
                    'id': visit.id,
                    'visit_date': visit.visit_date.isoformat(),
                    'visit_reason': visit.visit_reason,
                    'symptoms': visit.symptoms,
                    'status': visit.status
                }
                for visit in visits
            ]
        }
        
        if insurance:
            result['insurance'] = {
                'insurance_name': insurance.insurance_name,
                'medications': insurance.medications,
                'medical_conditions': insurance.medical_conditions
            }
            # 只有staff可以看保险ID
            if g.user_role == 'staff' and insurance.encrypted_insurance_id:
                result['insurance']['insurance_id'] = decrypt_data(insurance.encrypted_insurance_id)
        
        # 记录审计日志
        log_action('view', 'patient', patient_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_bp.route('/me', methods=['GET'])
@require_auth
@require_role('patient')
def get_my_info():
    """
    获取当前登录患者的信息
    """
    try:
        patient = Patient.query.filter_by(user_id=g.user_id).first()
        if not patient:
            return jsonify({'error': 'Patient record not found'}), 404
        
        # 获取就诊记录
        visits = Visit.query.filter_by(patient_id=patient.id)\
            .order_by(Visit.visit_date.desc()).limit(5).all()
        
        result = {
            'full_name': patient.full_name,
            'date_of_birth': patient.date_of_birth.isoformat(),
            'phone': patient.phone,
            'recent_visits': [
                {
                    'visit_date': visit.visit_date.isoformat(),
                    'visit_reason': visit.visit_reason,
                    'status': visit.status
                }
                for visit in visits
            ]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500