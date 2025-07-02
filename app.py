import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from PIL import Image, ImageTk
from io import BytesIO
import base64
import time
import json

# --- CONFIGURACIÓN ---
SERVER_URL = "https://edikpiccx-backend.onrender.com"
DRIVE_FOLDER_ID = "1Tux8uqv--gJjUc9_HrSZZEHsRyuzdJGO" 

# --- LOGGER PARA TERMINAL ---
class Logger:
    @staticmethod
    def info(message): print(f"[INFO] {time.strftime('%H:%M:%S')} - {message}")
    @staticmethod
    def error(message): print(f"[ERROR] {time.strftime('%H:%M:%S')} - {message}")
    @staticmethod
    def debug(message, data=None):
        print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {message}")
        if data: print(json.dumps(data, indent=2))

# --- APLICACIÓN PRINCIPAL (VERSIÓN SIMPLIFICADA) ---
class ControlPanelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panel de Control v4.0 (Simplificado y Robusto)")
        self.geometry("1200x700")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.agents_data = []
        self.photo_references = []
        self.create_widgets()
        self.threaded_task(self.refresh_agent_list)

    def create_widgets(self):
        # ... (Pega aquí el código completo de create_widgets que ya tenías y funcionaba)
        # La versión con PanedWindow, Treeview, Frames de comandos, Canvas, etc.
        pass

    def threaded_task(self, task, *args):
        thread = threading.Thread(target=task, args=args, daemon=True)
        thread.start()

    def refresh_agent_list(self):
        self.update_status("Contactando al servidor...", "blue")
        Logger.info("Solicitando lista de agentes al servidor...")
        try:
            response = requests.get(f"{SERVER_URL}/api/get-agents", timeout=10)
            response.raise_for_status()
            agents = response.json()
            Logger.debug("Respuesta del servidor (get-agents):", agents)
            self.after(0, self._update_treeview, agents)
            self.after(0, self.update_status, "Lista de agentes actualizada.", "green")
        except requests.exceptions.RequestException as e:
            Logger.error(f"No se pudo conectar al servidor: {e}")
            self.after(0, self.update_status, f"Error de conexión. ¿Está el servidor activo?", "red")

    def _update_treeview(self, agents):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.agents_data = agents
        if not agents:
            Logger.info("No hay agentes conectados en este momento.")
        for agent in agents:
            self.tree.insert('', tk.END, iid=agent['id'], values=(agent['id'], agent.get('name', 'N/A')))

    # El resto de las funciones de lógica (visualize_selected_device_files, on_command_click, etc.)
    # pueden quedarse como en la versión anterior. La lógica de "health_check" ha sido eliminada.
    # ... (Pega aquí el resto de las funciones lógicas que ya funcionaban)

if __name__ == "__main__":
    Logger.info("Iniciando Panel de Control...")
    app = ControlPanelApp()
    app.mainloop()
    Logger.info("Panel de Control cerrado.")
