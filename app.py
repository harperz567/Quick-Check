from flask import Flask, request, render_template, jsonify, redirect, url_for
import json
import os

app = Flask(__name__)

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

# 欢迎页面路由
@app.route('/')
def welcome():
    return render_template('welcome.html')

# 扫描选项页面路由
@app.route('/scan_options')
def scan_options():
    return render_template('scan_options.html')

# 手动输入页面路由
@app.route('/manual_entry')
def manual_entry():
    return render_template('manual_entry.html')

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
    
    # 重定向到确认页面
    return redirect(url_for('confirmation'))

# 确认页面
@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

# 检查病人API (可选，如果需要前端AJAX)
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