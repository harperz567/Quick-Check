from flask import Flask, request, render_template, jsonify, redirect, url_for, session, send_from_directory
import json
import os
import wave
import time
import threading
import pyaudio
import assemblyai as aai
from openai import OpenAI
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session to work
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'recordings'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
# API key
aai.settings.api_key = "22fa4a1dec48432788774b3950b66ca0"
transcriber = aai.Transcriber()
PERPLEXITY_API_KEY = "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"


# Make sure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

PATIENT_DATA_FILE = 'patients.txt'

# Load patient data
def load_patient_data():
    if os.path.exists(PATIENT_DATA_FILE):
        try:
            with open(PATIENT_DATA_FILE, 'r', encoding='utf-8') as file:
                return json.loads(file.read())
        except Exception as e:
            print(f"加载数据错误: {e}")
            return {}
    return {}

# Save data
def save_patient_data(patient_info):
    with open(PATIENT_DATA_FILE, 'w', encoding='utf-8') as file:
        file.write(json.dumps(patient_info, ensure_ascii=False))

# 1.Welcome page
@app.route('/')
def welcome():
    session.clear()  # Clear all previous data
    return render_template('welcome.html')

# 2.Scan page
@app.route('/scan_options')
def scan_options():
    return render_template('scan_options.html')

# Modify the manual_entry function to ensure that the birthday information is also passed to the template
@app.route('/manual_entry')
def manual_entry():
    # If session has data, prepopulate
    # delete this !!!!!!!!!!!!
    name = session.get('name', '')
    dob = session.get('dob', '')
    return render_template('manual_entry.html', name=name, dob=dob)


# Update welcome_confirmation 
@app.route('/welcome_confirmation', methods=['POST'])
def welcome_confirmation():
    name = request.form.get('name', '')
    dob = request.form.get('dob', '')  
    
    # Save into session
    session['name'] = name
    if dob:  
        session['dob'] = dob
    
    return render_template('welcome_confirmation.html', name=name)



# 6.
@app.route('/insurance_options')
def insurance_options():
    return render_template('insurance_options.html')

# 7.
@app.route('/manual_insurance')
def manual_insurance():
    return render_template('manual_insurance.html')

# 8.
@app.route('/reason_for_visit')
def reason_for_visit():
    return render_template('reason_for_visit.html')

# 9. Voice input page
@app.route('/voice_input')
def voice_input():
    return render_template('voice_input.html')

# Text input page
@app.route('/text_input')
def text_input():
    return render_template('text_input.html')

# Voice processing API
@app.route('/api/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save audio file
    filename = secure_filename(f"recording_{int(time.time())}.wav")
    file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
    audio_file.save(file_path)
    
    # Process audio file
    try:
        # Convert audio to text
        text = assembly(file_path)
        
        # Analyze symptoms
        analysis = perplex(text)
        
        # Get patient name (if available in session)
        patient_name = session.get('name', '')
        
        # Save analysis results to local file
        analysis_filename = save_analysis_to_file(patient_name, text, analysis)
        
        # Save to session
        session['voice_text'] = text
        session['symptoms_analysis'] = analysis
        session['visit_reason'] = text  # Use voice content as visit reason
        session['analysis_filename'] = analysis_filename  # Save filename for future reference
        
        if isinstance(analysis, dict):
            session['symptoms'] = ", ".join(analysis.get('symptoms', []))
        
        return jsonify({
            'success': True, 
            'text': text, 
            'analysis': analysis,
            'analysis_file': analysis_filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Add route for accessing analysis files
@app.route('/analysis_files/<filename>')
def get_analysis_file(filename):
    """
    Access saved symptom analysis files
    """
    ANALYSIS_FOLDER = 'patient_analysis'
    return send_from_directory(ANALYSIS_FOLDER, filename)

# Updated confirmation route that passes analysis filename
@app.route('/confirmation')
def confirmation():
    # Get analysis results
    analysis = session.get('symptoms_analysis', {})
    possible_causes = []
    
    if isinstance(analysis, dict):
        possible_causes = analysis.get('possible causes', [])
    
    return render_template('confirmation.html', 
                          name=session.get('name', ''),
                          insurance_name=session.get('insurance_name', ''),
                          insurance_id=session.get('insurance_id', ''),
                          medications=session.get('medications', ''),
                          conditions=session.get('conditions', ''),
                          visit_reason=session.get('visit_reason', ''),
                          symptoms=session.get('symptoms', ''),
                          possible_causes=possible_causes,
                          analysis_filename=session.get('analysis_filename', ''))

# AssemblyAI turn audio into txt file
def assembly(audio):
    transcript = transcriber.transcribe(audio)
    text = transcript.text
    print(f"转录结果: {text}")
    return text


def perplex(text):
    messages = [
        {
            "role" : "system",
            "content":(
                "You are an artificial intelligence assistant for hospital patients. "
                "You need to analyze the patient's symptoms and provide possible causes. "
                "The response MUST be a valid Python dictionary with exactly this format: "
                "{'symptoms': ['symptom 1', 'symptom 2', ...], 'possible causes': ['cause 1', 'cause 2', ...]}. "
                "Analyze the symptoms a patient is experiencing in detail (how severe the pain is and how long it has been). "
                "Do not include any explanation or additional text - ONLY the Python dictionary."
            ),
        },
        {
            "role": "user",
            "content": text
        }
    ]

    client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    summary = response.choices[0].message.content
    print(f"API response: {summary}")
    
    try:
        # Try to parse the response using a safer method
        import json
        # Try to find the beginning and end of the dictionary
        start_idx = summary.find('{')
        end_idx = summary.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            dict_str = summary[start_idx:end_idx]
            # Use json parsing instead of eval
            result = json.loads(dict_str.replace("'", "\""))
            
            # Ensure the result contains necessary keys
            if 'symptoms' not in result:
                result['symptoms'] = []
            if 'possible causes' not in result:
                result['possible causes'] = []
                
            return result
    except Exception as e:
        print(f"Error parsing API response: {e}")
    
    # Return default structure if parsing fails
    return {
        'symptoms': ['Unable to extract clear symptoms from description'],
        'possible causes': ['Please consult a doctor for accurate diagnosis']
    }


def save_analysis_to_file(patient_name, text, analysis):
    """
    Save voice transcription and symptom analysis to a local file
    
    Args:
        patient_name: Patient name
        text: Voice transcription text
        analysis: Symptom analysis result
    """
    import os
    import json
    import datetime
    
    # Create directory for analysis storage
    ANALYSIS_FOLDER = 'patient_analysis'
    if not os.path.exists(ANALYSIS_FOLDER):
        os.makedirs(ANALYSIS_FOLDER)
    
    # Get patient name from parameter and DOB from session if available
    patient_dob = session.get('dob', '')
    
    # Generate filename with name-dob-date format
    today_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Clean up the name and DOB for use in filename
    safe_name = ''.join(c if c.isalnum() else '·' for c in patient_name) if patient_name else "unknown"
    # Keep only alphabetic and numeric characters, directly remove all other characters
    safe_dob = ''.join(c for c in patient_dob if c.isalnum()) if patient_dob else "nodob"

    # Create filename: name-dob-date.txt
    filename = f"{safe_name}-{safe_dob}-{today_date}.txt"
    filepath = os.path.join(ANALYSIS_FOLDER, filename)
    
    # Format symptoms and possible causes
    symptoms = []
    causes = []
    
    if isinstance(analysis, dict):
        symptoms = analysis.get('symptoms', [])
        causes = analysis.get('possible causes', [])
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Patient Name: {patient_name}\n")
        f.write(f"Patient DOB: {patient_dob}\n")
        f.write(f"Record Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=== Patient Description ===\n")
        f.write(f"{text}\n\n")
        f.write("=== Symptom Analysis ===\n")
        
        if symptoms:
            f.write("Symptoms:\n")
            for symptom in symptoms:
                f.write(f"- {symptom}\n")
        else:
            f.write("No specific symptoms identified\n")
        
        f.write("\nPossible Causes:\n")
        if causes:
            for cause in causes:
                f.write(f"- {cause}\n")
        else:
            f.write("No specific causes determined\n")
    
    print(f"Analysis result saved to: {filepath}")
    return filename




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

# Start recording
@app.route('/api/start_recording', methods=['POST'])
def start_recording():
    # This API will be called from the frontend to initiate the recording feature
    # Since we can't directly launch the recording interface on the server side, this functionality needs to be implemented via frontend JavaScript
    # Here is only returns a success flag, indicating that the server is ready to receive the recording
    return jsonify({'status': 'ready'})

# Fetch recording
@app.route('/recordings/<filename>')
def get_recording(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.route('/submit_info', methods=['POST'])
def submit_info():
    name = request.form.get('name')
    dob = request.form.get('dob')
    
    if not name or not dob:
        return "Name and date of birth is required", 400
    
    # Save name and dob in session 
    session['name'] = name
    session['dob'] = dob
    
    # Upload data
    patient_info = load_patient_data()
    
    # Add patient if not exist
    if name not in patient_info:
        patient_info[name] = {}
        
    if dob not in patient_info[name]:
        patient_info[name][dob] = []
    
    # Save data 
    save_patient_data(patient_info)
    return render_template('welcome_confirmation.html', name=name)


# # Check patient 
# @app.route('/api/check_patient', methods=['POST'])
# def check_patient():
#     data = request.json
#     name = data.get('name')
#     dob = data.get('dob')
    
#     patient_info = load_patient_data()
    
#     if name in patient_info and dob in patient_info[name]:
#         return jsonify({"exists": True})
#     else:
#         return jsonify({"exists": False})

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)