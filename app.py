# app.py pour la Raspberry Pi
from flask import Flask, Response
import io
import picamera
import time
import threading
import socket

app = Flask(__name__)

# Configuration de la caméra
camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.framerate = 24
camera.rotation = 0

# Buffer pour stocker les images
output = io.BytesIO()

# Fonction pour générer le flux vidéo
def generate_frames():
    while True:
        output.seek(0)
        output.truncate()
        camera.capture(output, format='jpeg', use_video_port=True)
        frame = output.getvalue()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route pour diffuser le flux vidéo
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Page d'accueil
@app.route('/')
def index():
    ip = socket.gethostbyname(socket.gethostname())
    return f"""
    <html>
      <head>
        <title>Détection d'incendies - Raspberry Pi</title>
      </head>
      <body>
        <h1>Flux vidéo de la Raspberry Pi</h1>
        <img src="/video_feed" width="640" height="480" />
        <p>URL du flux vidéo: http://{ip}:5000/video_feed</p>
      </body>
    </html>
    """

if __name__ == '__main__':
    # Obtenir l'adresse IP de la Raspberry Pi
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Serveur démarré sur http://{ip}:5000")
    # Démarrer le serveur Flask accessible depuis d'autres appareils sur le réseau
    app.run(host='0.0.0.0', port=5000, threaded=True)
