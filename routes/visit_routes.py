from flask import request, jsonify, g
from routes import visit_bp
from models import db, Visit, Patient
from auth.decorators import require_auth, require_role
from security.audit import log_action

@visit_bp.route('/recent', methods=['GET'])
@require_auth
@require_role('staff')
def get_recent_visits():
    """
    获取最近的就诊记录 - 仅staff可访问
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        visits = Visit.query\
            .join(Patient)\
            .order_by(Visit.visit_date.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for visit in visits:
            result.append({
                'id': visit.id,
                'patient_id': visit.patient_id,
                'patient_name': visit.patient.full_name,
                'visit_date': visit.visit_date.isoformat(),
                'visit_reason': visit.visit_reason,
                'symptoms': visit.symptoms,
                'status': visit.status
            })
        
        log_action('view', 'visit_list', details={'count': len(result)})
        
        return jsonify({'visits': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visit_bp.route('/<int:visit_id>', methods=['GET'])
@require_auth
def get_visit(visit_id):
    """
    获取就诊详情
    - 患者只能查看自己的
    - Staff可以查看所有
    """
    try:
        visit = Visit.query.get(visit_id)
        if not visit:
            return jsonify({'error': 'Visit not found'}), 404
        
        # 权限检查
        if g.user_role == 'patient':
            patient = Patient.query.filter_by(user_id=g.user_id).first()
            if not patient or visit.patient_id != patient.id:
                return jsonify({'error': 'Access denied'}), 403
        
        result = {
            'id': visit.id,
            'patient_name': visit.patient.full_name,
            'visit_date': visit.visit_date.isoformat(),
            'visit_reason': visit.visit_reason,
            'voice_transcription': visit.voice_transcription,
            'symptoms': visit.symptoms,
            'possible_causes': visit.possible_causes,
            'pain_level': visit.pain_level,
            'pain_duration': visit.pain_duration,
            'status': visit.status,
            'audio_file': visit.audio_file_path,
            'analysis_file': visit.analysis_file_path
        }
        
        log_action('view', 'visit', visit_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visit_bp.route('/my-visits', methods=['GET'])
@require_auth
@require_role('patient')
def get_my_visits():
    """
    获取当前患者的所有就诊记录
    """
    try:
        patient = Patient.query.filter_by(user_id=g.user_id).first()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        visits = Visit.query.filter_by(patient_id=patient.id)\
            .order_by(Visit.visit_date.desc())\
            .all()
        
        result = [
            {
                'id': visit.id,
                'visit_date': visit.visit_date.isoformat(),
                'visit_reason': visit.visit_reason,
                'symptoms': visit.symptoms,
                'status': visit.status
            }
            for visit in visits
        ]
        
        return jsonify({'visits': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500