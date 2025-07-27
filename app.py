# app.py (para el repositorio edikpiccx)
from flask import Flask, redirect

app = Flask(__name__)

@app.route('/')
@app.route('/<path:path>')
def redirect_to_frontend(path=None):
    """
    Redirecciona TODAS las peticiones a la app de GitHub Pages.
    """
    return redirect("https://denverdesign.github.io/edikpiccx/", code=301)
