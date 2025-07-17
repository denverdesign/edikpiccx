from flask import Flask, render_template, send_from_directory, abort
import os

# Creamos la instancia de la aplicación Flask
app = Flask(__name__)

# Ruta principal que muestra tu editor de fotos
@app.route('/')
def home():
    """
    Sirve el archivo 'index.html'. Flask lo buscará en una carpeta 'templates'.
    """
    return render_template('index.html')

# Ruta para descargar el agente
@app.route('/download/agent')
def download_agent():
    """
    Sirve el archivo 'agente.apk' desde la carpeta 'public'.
    """
    try:
        # Asegúrate de que tu APK se llame 'agente.apk' y esté en una carpeta 'public'
        return send_from_directory('public', 'agente.apk', as_attachment=True)
    except FileNotFoundError:
        abort(404)

# Este bloque es opcional para Render, pero bueno para pruebas locales.
# Gunicorn llamará directamente a la variable 'app'.
if __name__ == '__main__':
    # Usamos el puerto que Render nos asigne a través de la variable de entorno
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
