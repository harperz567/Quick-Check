import assemblyai as aai
from openai import OpenAI
from flask import current_app
import json
import os
from datetime import datetime

def process_audio_file(audio_path: str) -> dict:
    """
    处理音频文件：转录 + 症状分析
    
    Returns:
        {
            'text': '转录文本',
            'analysis': {'symptoms': [...], 'possible causes': [...]},
            'analysis_filename': '分析文件名'
        }
    """
    # 1. 语音转文字（AssemblyAI）
    text = transcribe_audio(audio_path)
    
    # 2. 症状分析（Perplexity AI）
    analysis = analyze_symptoms(text)
    
    # 3. 保存分析结果
    filename = save_analysis(text, analysis)
    
    return {
        'text': text,
        'analysis': analysis,
        'analysis_filename': filename
    }

def transcribe_audio(audio_path: str) -> str:
    """使用AssemblyAI转录音频"""
    aai.settings.api_key = current_app.config['ASSEMBLYAI_API_KEY']
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path)
    
    return transcript.text

def analyze_symptoms(text: str) -> dict:
    """使用Perplexity AI分析症状"""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant for hospital patients. "
                "You need to analyze the patient's symptoms and provide possible causes. "
                "The response MUST be a valid JSON object with exactly this format: "
                '{"symptoms": ["symptom 1", "symptom 2", ...], "possible causes": ["cause 1", "cause 2", ...]}. '
                "Analyze the symptoms in detail (severity and duration). "
                "Do not include any explanation or additional text - ONLY the JSON object."
            ),
        },
        {
            "role": "user",
            "content": text
        }
    ]
    
    client = OpenAI(
        api_key=current_app.config['PERPLEXITY_API_KEY'],
        base_url="https://api.perplexity.ai"
    )
    
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    
    summary = response.choices[0].message.content
    
    try:
        # 解析JSON响应
        start_idx = summary.find('{')
        end_idx = summary.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            dict_str = summary[start_idx:end_idx]
            result = json.loads(dict_str.replace("'", "\""))
            
            # 确保包含必要的键
            if 'symptoms' not in result:
                result['symptoms'] = []
            if 'possible causes' not in result:
                result['possible causes'] = []
            
            return result
    except Exception as e:
        print(f"Error parsing AI response: {e}")
    
    # 解析失败时返回默认结构
    return {
        'symptoms': ['Unable to extract clear symptoms'],
        'possible causes': ['Please consult a doctor for accurate diagnosis']
    }

def save_analysis(text: str, analysis: dict) -> str:
    """保存分析结果到文件"""
    ANALYSIS_FOLDER = current_app.config['ANALYSIS_FOLDER']
    
    if not os.path.exists(ANALYSIS_FOLDER):
        os.makedirs(ANALYSIS_FOLDER)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{timestamp}.txt"
    filepath = os.path.join(ANALYSIS_FOLDER, filename)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Record Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=== Patient Description ===\n")
        f.write(f"{text}\n\n")
        f.write("=== Symptom Analysis ===\n")
        
        symptoms = analysis.get('symptoms', [])
        if symptoms:
            f.write("Symptoms:\n")
            for symptom in symptoms:
                f.write(f"- {symptom}\n")
        
        f.write("\nPossible Causes:\n")
        causes = analysis.get('possible causes', [])
        if causes:
            for cause in causes:
                f.write(f"- {cause}\n")
    
    return filename