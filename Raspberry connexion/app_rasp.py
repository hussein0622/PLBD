# app.py pour la Raspberry Pi
from flask import Flask, Response
import io
from picamera2 import Picamera2
import time
import threading
import socket
import numpy as np
import cv2

app = Flask(__name__)

# Configuration de la caméra avec Picamera2
camera = Picamera2()
camera_config = camera.create_preview_configuration(main={"size": (640, 480)})
camera.configure(camera_config)
camera.start()

# Fonction pour capturer une image et la convertir en JPEG
def capture_jpeg():
    frame = camera.capture_array()
    # Convertir en BGR (si nécessaire) puis en JPEG
    if len(frame.shape) == 2:  # Si l'image est en niveaux de gris
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()

# Fonction pour générer le flux vidéo
def generate_frames():
    while True:
        frame = capture_jpeg()
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
    # Tentative d'obtenir l'adresse IP locale
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "localhost"
        
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
    # Attendre que la caméra s'initialise
    time.sleep(2)
    
    # Tentative d'obtenir l'adresse IP locale
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "localhost"
        
    print(f"Serveur démarré sur http://{ip}:5000")
    # Démarrer le serveur Flask accessible depuis d'autres appareils sur le réseau
    app.run(host='0.0.0.0', port=5000, threaded=True)
