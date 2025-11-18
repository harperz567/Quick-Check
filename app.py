from flask import Flask, render_template, redirect, url_for, request, jsonify, session, send_from_directory, g
from werkzeug.utils import secure_filename
from config import config
from models import db
from flask_migrate import Migrate
import os
import time
import json
from datetime import datetime
from auth.decorators import require_auth, require_auth_page, require_role

# 创建Flask应用
app = Flask(__name__)

# 加载配置
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# 初始化数据库
db.init_app(app)
migrate = Migrate(app, db)

# 注册蓝图
from routes import auth_bp, patient_bp, visit_bp
app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(visit_bp)

# 确保文件夹存在
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
AUDIO_FOLDER = app.config['AUDIO_FOLDER']
ANALYSIS_FOLDER = app.config['ANALYSIS_FOLDER']

for folder in [UPLOAD_FOLDER, AUDIO_FOLDER, ANALYSIS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==================== 页面路由 ====================

@app.route('/')
def index():
    """首页 - 重定向到登录"""
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """注册页面"""
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard - Staff专用"""
    return render_template('dashboard.html')

@app.route('/patient/welcome')
def patient_welcome():
    """患者欢迎页 - 登录后进入"""
    return render_template('patient_welcome.html')

# ==================== 患者登记流程路由（需要认证）====================

from auth.decorators import require_auth, require_role

@app.route('/insurance_options')
@require_auth_page
def insurance_options():
    """保险选项"""
    return render_template('insurance_options.html')

@app.route('/manual_insurance')
@require_auth_page
def manual_insurance():
    """手动输入保险信息"""
    return render_template('manual_insurance.html')

@app.route('/submit_insurance', methods=['POST'])
@require_auth
def submit_insurance():
    """提交保险信息"""
    from models import Patient, Insurance
    from security.encryption import encrypt_data
    from security.audit import log_action
    
    # 获取当前患者
    patient = Patient.query.filter_by(user_id=g.user_id).first()
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # 处理保险信息
    insurance = Insurance.query.filter_by(patient_id=patient.id).first()
    if not insurance:
        insurance = Insurance(patient_id=patient.id)
    
    insurance.insurance_name = request.form.get('insurance_name', '')
    insurance_id = request.form.get('insurance_id', '')
    if insurance_id:
        insurance.encrypted_insurance_id = encrypt_data(insurance_id)
    
    insurance.medications = request.form.get('medications', '')
    insurance.medical_conditions = request.form.get('conditions', '')
    
    db.session.add(insurance)
    db.session.commit()
    
    # 记录审计日志
    log_action('update', 'insurance', insurance.id)
    
    return render_template('insurance_success.html')

@app.route('/reason_for_visit')
@require_auth_page
def reason_for_visit():
    """就诊原因选择"""
    return render_template('reason_for_visit.html')

@app.route('/submit_reason', methods=['POST'])
@require_auth
def submit_reason():
    """提交就诊原因（从语音或文本输入）"""
    reason = request.form.get('reason', '')
    session['visit_reason'] = reason
    return redirect(url_for('pain_assessment'))

@app.route('/voice_input')
@require_auth_page
def voice_input():
    """语音输入"""
    return render_template('voice_input.html')

@app.route('/text_input')
@require_auth_page
def text_input():
    """文本输入"""
    return render_template('text_input.html')

@app.route('/api/process_audio', methods=['POST'])
@require_auth
def process_audio():
    """处理语音文件 - AI分析"""
    from services.ai_service import process_audio_file
    from models import Patient, Visit
    from security.audit import log_action
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # 保存音频文件
    filename = secure_filename(f"recording_{int(time.time())}.wav")
    file_path = os.path.join(AUDIO_FOLDER, filename)
    audio_file.save(file_path)
    
    try:
        # 使用AI服务处理音频
        result = process_audio_file(file_path)
        
        # 获取当前患者
        patient = Patient.query.filter_by(user_id=g.user_id).first()
        
        # 创建就诊记录
        visit = Visit(
            patient_id=patient.id,
            visit_reason=result['text'],
            voice_transcription=result['text'],
            symptoms=result['analysis'].get('symptoms', []),
            possible_causes=result['analysis'].get('possible causes', []),
            audio_file_path=filename,
            analysis_file_path=result['analysis_filename']
        )
        db.session.add(visit)
        db.session.commit()
        
        # 记录审计日志
        log_action('create', 'visit', visit.id, {
            'patient_id': patient.id,
            'has_audio': True
        })
        
        # 保存到session（用于后续页面）
        session['current_visit_id'] = visit.id
        session['visit_reason'] = result['text']
        session['symptoms'] = ", ".join(result['analysis'].get('symptoms', []))
        
        return jsonify({
            'success': True,
            'text': result['text'],
            'analysis': result['analysis'],
            'analysis_file': result['analysis_filename']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pain_assessment')
@require_auth_page
def pain_assessment():
    """疼痛评估"""
    return render_template('pain_assessment.html')

@app.route('/submit_pain_assessment', methods=['POST'])
@require_auth
def submit_pain_assessment():
    """提交疼痛评估"""
    from models import Visit
    
    pain_level = request.form.get('pain_level', '5')
    duration = request.form.get('duration', 'day')
    
    # 更新当前就诊记录
    visit_id = session.get('current_visit_id')
    if visit_id:
        visit = Visit.query.get(visit_id)
        if visit:
            visit.pain_level = int(pain_level)
            visit.pain_duration = duration
            db.session.commit()
    
    session['pain_level'] = pain_level
    session['duration'] = duration
    
    return redirect(url_for('visit_confirmation'))

@app.route('/visit_confirmation')
@require_auth_page
def visit_confirmation():
    """就诊确认"""
    return render_template('visit_confirmation.html',
                          visit_reason=session.get('visit_reason', ''),
                          symptoms=session.get('symptoms', ''),
                          pain_level=session.get('pain_level', '5'),
                          duration=session.get('duration', 'day'))

@app.route('/submit_confirmation', methods=['POST'])
@require_auth
def submit_confirmation():
    """提交最终确认"""
    from models import Visit
    
    # 更新就诊状态
    visit_id = session.get('current_visit_id')
    if visit_id:
        visit = Visit.query.get(visit_id)
        if visit:
            visit.status = 'confirmed'
            db.session.commit()
    
    return redirect(url_for('appointment_confirmation'))

@app.route('/appointment_confirmation')
@require_auth_page
def appointment_confirmation():
    """预约确认"""
    return render_template('appointment_confirmation.html')

# ==================== 文件访问路由 ====================

@app.route('/recordings/<filename>')
def get_recording(filename):
    """获取录音文件"""
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/analysis_files/<filename>')
def get_analysis_file(filename):
    """获取分析文件"""
    return send_from_directory(ANALYSIS_FOLDER, filename)

# ==================== 错误处理 ====================

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== 运行应用 ====================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)