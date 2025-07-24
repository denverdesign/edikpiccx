import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# La 'SECRET_KEY' es necesaria para SocketIO
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-segura!')
# Usamos el modo 'threading' que es compatible con gunicorn
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Diccionario para mantener un registro de los agentes conectados
# La clave es el 'sid' de la conexión, el valor son los datos del agente
connected_agents = {}

# --- RUTAS HTTP (Para el Panel de Control) ---

@app.route('/')
def serve_index():
    # Esta ruta puede servir una página de estado si lo deseas
    return "Servidor Backend Activo"

@app.route('/api/get-agents', methods=['GET'])
def get_agents():
    """
    Endpoint para que el panel de control obtenga la lista de agentes.
    """
    # Devolvemos una lista de los valores del diccionario de agentes
    return jsonify(list(connected_agents.values()))

@app.route('/api/send-command', methods=['POST'])
def send_command_to_agent():
    """
    Endpoint para que el panel de control envíe un comando a un agente específico.
    """
    data = request.json
    target_sid = data.get('target_id') # En el panel, el 'id' del agente es su 'sid'
    action = data.get('action')
    payload = data.get('payload', '')

    if not target_sid or not action:
        return jsonify({"status": "error", "message": "Faltan target_id o action"}), 400

    if target_sid not in connected_agents:
        return jsonify({"status": "error", "message": "Agente no encontrado o desconectado"}), 404

    # Usamos socketio.emit para enviar el comando al cliente correcto
    # El evento se llama 'server_command', que la app de Android debe escuchar
    socketio.emit('server_command', {'command': action, 'payload': payload}, to=target_sid)
    
    print(f"[COMANDO] Enviando '{action}' al agente {connected_agents[target_sid].get('name')}")
    return jsonify({"status": "success", "message": f"Comando '{action}' enviado."})

@app.route('/api/media-upload', methods=['POST'])
def handle_media_upload():
    """
    Endpoint para que el agente de Android envíe las miniaturas.
    (Esta es una implementación posible, necesitarías añadir la lógica de Google Drive aquí)
    """
    data = request.json
    agent_id = data.get('agent_id')
    files = data.get('files')
    print(f"Recibidas {len(files)} miniaturas del agente {agent_id}")
    # Aquí iría tu lógica para subir los archivos a Google Drive o almacenarlos temporalmente
    return jsonify({"status": "success"})


# --- EVENTOS DE WEBSOCKET (Para los Agentes de Android) ---

@socketio.on('connect')
def handle_connect():
    """
    Se ejecuta cuando un nuevo agente de Android se conecta.
    """
    # El 'sid' es un ID de sesión único que SocketIO asigna a cada cliente
    sid = request.sid
    device_name = request.args.get('deviceName', 'Dispositivo Desconocido')
    
    # Guardamos la información del agente
    connected_agents[sid] = {
        'id': sid, # Usamos el sid como ID único del agente
        'name': device_name,
        'status': 'connected'
    }
    print(f"[CONEXIÓN] Nuevo agente conectado: {device_name} (ID: {sid})")
    # Opcional: notificar al panel de control que un nuevo agente se conectó

@socketio.on('disconnect')
def handle_disconnect():
    """
    Se ejecuta cuando un agente de Android se desconecta.
    """
    sid = request.sid
    agent_info = connected_agents.pop(sid, None)
    if agent_info:
        print(f"[DESCONEXIÓN] Agente desconectado: {agent_info.get('name')} (ID: {sid})")
    # Opcional: notificar al panel de control que un agente se desconectó

@socketio.on('agent_response')
def handle_agent_response(data):
    """
    Escucha respuestas genéricas que el agente pueda enviar.
    """
    sid = request.sid
    agent_name = connected_agents.get(sid, {}).get('name', 'Desconocido')
    print(f"Respuesta recibida del agente {agent_name}: {data}")


# --- INICIALIZACIÓN ---
if __name__ == '__main__':
    print("Iniciando servidor Flask con SocketIO...")
    # El host '0.0.0.0' es necesario para que sea accesible desde fuera del contenedor
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
