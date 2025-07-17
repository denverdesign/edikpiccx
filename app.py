from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

# Ruta principal que muestra tu editor de fotos
@app.route('/')
def home():
    """
    Esta función sirve el archivo 'index.html' cuando alguien visita la página principal.
    """
    return render_template('index.html')

# Ruta para descargar el agente
@app.route('/download/agent')
def download_agent():
    """
    Esta función se activa cuando se hace clic en el botón de descarga.
    Busca el archivo 'agente.apk' dentro de una carpeta 'public' y lo envía al usuario.
    """
    try:
        # Asegúrate de que tu APK se llame 'agente.apk' y esté en una carpeta 'public'
        return send_from_directory('public', 'agente.apk', as_attachment=True)
    except FileNotFoundError:
        # Si no se encuentra el archivo, devuelve un error 404
        abort(404)

if __name__ == '__main__':
    # Este bloque permite ejecutar el servidor localmente para pruebas
    app.run(debug=True)
