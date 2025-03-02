from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session to work
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 数据文件路径
PATIENT_DATA_FILE = 'patients.txt'

# 加载病人数据
def load_patient_data():
    if os.path.exists(PATIENT_DATA_FILE):
        try:
            with open(PATIENT_DATA_FILE, 'r', encoding='utf-8') as file:
                return json.loads(file.read())
        except Exception as e:
            print(f"加载数据错误: {e}")
            return {}
    return {}

# 保存病人数据
def save_patient_data(patient_info):
    with open(PATIENT_DATA_FILE, 'w', encoding='utf-8') as file:
        file.write(json.dumps(patient_info, ensure_ascii=False))

# 1.欢迎页面路由
@app.route('/')
def welcome():
    return render_template('welcome.html')

# 2.扫描选项页面路由
@app.route('/scan_options')
def scan_options():
    
    return render_template('scan_options.html')

# 3.
# @app.route('/scan')
# def scan():
#     return render_template('scan_id.html')
# 缺HTML

# 4.手动输入页面路由
@app.route('/manual_entry')
def manual_entry():

    return render_template('manual_entry.html')

# 5.
@app.route('/welcome_confirmation', methods=['POST'])
def welcome_confirmation():
    name = request.form.get('name', '')
    session['name'] = name
    return render_template('welcome_confirmation.html', name=name)
# 6.
@app.route('/insurance_options')
def insurance_options():
    return render_template('insurance_options.html')
# 7.
@app.route('/manual_insurance')
def manual_insurance():
    return render_template('manual_insurance.html')
#8.
@app.route('/reason_for_visit')
def reason_for_visit():
    return render_template('reason_for_visit.html')
# 9.
@app.route('/voice_input')
def voice_input():
    return render_template('voice_input.html')
@app.route('/text_input')
def text_input():
    return render_template('text_input.html')

@app.route('/submit_reason', methods=['POST'])
def submit_reason():
    reason = request.form.get('reason', '')
    session['visit_reason'] = reason
    return redirect(url_for('pain_assessment'))

@app.route('/pain_assessment')
def pain_assessment():
    return render_template('pain_assessment.html')

@app.route('/submit_pain_assessment', methods=['POST'])
def submit_pain_assessment():
    pain_level = request.form.get('pain_level', '5')
    duration = request.form.get('duration', 'day')
    
    session['pain_level'] = pain_level
    session['duration'] = duration
    
    return redirect(url_for('visit_confirmation'))

@app.route('/visit_confirmation')
def visit_confirmation():
    return render_template('visit_confirmation.html',
                          visit_reason=session.get('visit_reason', ''),
                          symptoms=session.get('symptoms', ''),
                          pain_level=session.get('pain_level', '5'),
                          duration=session.get('duration', 'day'))

@app.route('/submit_confirmation', methods=['POST'])
def submit_confirmation():
    # Here you would typically save all the collected data to a database
    return redirect(url_for('appointment_confirmation'))

@app.route('/appointment_confirmation')
def appointment_confirmation():
    return render_template('appointment_confirmation.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html', 
                          name=session.get('name', ''),
                          insurance_name=session.get('insurance_name', ''),
                          insurance_id=session.get('insurance_id', ''),
                          medications=session.get('medications', ''),
                          conditions=session.get('conditions', ''),
                          visit_reason=session.get('visit_reason', ''))





@app.route('/submit_insurance', methods=['POST'])
def submit_insurance():
    if 'insurance_file' in request.files:
        file = request.files['insurance_file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['insurance_file'] = filename
    else:
        # Handle manual entry
        session['insurance_name'] = request.form.get('insurance_name', '')
        session['insurance_id'] = request.form.get('insurance_id', '')
    
    session['medications'] = request.form.get('medications', '')
    session['conditions'] = request.form.get('conditions', '')
    
    return render_template('insurance_success.html')




@app.route('/scan_insurance')
def scan_insurance():
    return render_template('scan_insurance.html')



# 提交病人信息处理
@app.route('/submit_info', methods=['POST'])
def submit_info():
    name = request.form.get('name')
    dob = request.form.get('dob')
    
    if not name or not dob:
        return "姓名和出生日期不能为空", 400
    
    # 加载现有数据
    patient_info = load_patient_data()
    
    # 将病人信息添加到系统（如果不存在）
    if name not in patient_info:
        patient_info[name] = {}
        
    if dob not in patient_info[name]:
        patient_info[name][dob] = []
    
    # 保存数据
    save_patient_data(patient_info)
    return render_template('welcome_confirmation.html', name=name)

# 确认页面
# @app.route('/confirmation')
# def confirmation():
#     return render_template('confirmation.html')

# 检查病人API (可选，如果需要前端AJAX)(Not avaliable)
@app.route('/api/check_patient', methods=['POST'])
def check_patient():
    data = request.json
    name = data.get('name')
    dob = data.get('dob')
    
    if not name or not dob:
        return jsonify({"error": "姓名和出生日期不能为空"}), 400
    
    patient_info = load_patient_data()
    
    if name in patient_info and dob in patient_info[name]:
        return jsonify({"exists": True})
    else:
        return jsonify({"exists": False})

if __name__ == '__main__':
    app.run(debug=True)