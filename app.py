import os
import json
import base64
import uuid
from flask import Flask, request, jsonify, send_from_directory
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import BytesIO

# Importamos la clase correcta para las credenciales de servicio
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN ---
DRIVE_FOLDER_ID = '1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO'
app = Flask(__name__)
pending_command = None
drive = None

# --- FUNCIÓN DE AUTENTICACIÓN (VERSIÓN CORREGIDA) ---
def authenticate_gdrive():
    """
    Versión final y correcta para autenticación con Cuentas de Servicio
    usando la librería google-auth directamente.
    """
    secrets_json_str = os.environ.get('GOOGLE_CLIENT_SECRETS')
    if not secrets_json_str:
        raise Exception("Variable de entorno 'GOOGLE_CLIENT_SECRETS' no encontrada.")
    
    # Cargamos el diccionario desde la cadena de texto JSON
    secrets_dict = json.loads(secrets_json_str)
    
    # Definimos los alcances (permisos) que necesitamos
    scopes = ['https://www.googleapis.com/auth/drive']
    
    # Creamos las credenciales directamente desde el diccionario de secretos
    credentials = Credentials.from_service_account_info(
        secrets_dict, 
        scopes=scopes
    )
    
    # Creamos el objeto de autenticación y le asignamos las credenciales
    gauth = GoogleAuth()
    gauth.credentials = credentials
    
    # Autorizamos (esto es opcional pero una buena práctica para asegurar que todo está bien)
    gauth.Authorize()
    
    # Devolvemos el objeto drive listo para usar
    return GoogleDrive(gauth)

# --- ENDPOINTS ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/download/agent')
def download_agent_apk():
    try:
        return send_from_directory('public', 'app-debug.apk', as_attachment=True)
    except FileNotFoundError:
        return "APK del agente no encontrado en la carpeta 'public'.", 404

@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch_photos():
    global pending_command
    pending_command = "GET_PHOTOS"
    print("[SERVER] Orden 'GET_PHOTOS' recibida y en cola.")
    return jsonify({"status": "success"})

@app.route('/get-command', methods=['GET'])
def get_command_for_agent():
    global pending_command
    print("[AGENT] Agente se ha reportado...")
    if pending_command:
        command_to_send = pending_command
        pending_command = None 
        print(f"[SERVER] -> Entregando orden '{command_to_send}' al agente.")
        return jsonify({"command": command_to_send})
    print("[SERVER] -> No hay órdenes pendientes.")
    return jsonify({"command": "NONE"})

@app.route('/upload', methods=['POST'])
def upload_to_drive():
    global drive
    if not drive:
        print("[ERROR] Intento de subida fallido: no hay conexión con Google Drive.")
        return jsonify({"status": "error", "message": "Conexión con Google Drive no inicializada."}), 503

    data = request.json
    if not data or 'files' not in data:
        return jsonify({"status": "error", "message": "Formato de datos incorrecto."}), 400

    print(f"[SERVER] Recibiendo {len(data.get('files', []))} archivos para subir a Drive...")
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

# --- BLOQUE DE INICIALIZACIÓN ---
# Se ejecuta solo una vez cuando el servidor arranca en Render.
with app.app_context():
    try:
        drive = authenticate_gdrive()
        print("Autenticación con Google Drive exitosa al arrancar.")
    except Exception as e:
        print(f"ERROR CRÍTICO AL ARRANCAR: {e}")
