# app_optimized.py pour la Raspberry Pi
from flask import Flask, Response
import cv2
import numpy as np
import socket
import time
import threading
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io

app = Flask(__name__)

# Configuration globale
frame_width = 640
frame_height = 480
fps = 15
quality = 80  # Qualité JPEG (0-100)

# Buffer circulaire pour le dernier frame
latest_frame = None
frame_lock = threading.Lock()

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = threading.Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # Nouveau frame JPEG
            self.buffer.seek(0)
            self.buffer.truncate()
            self.buffer.write(buf)
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
        else:
            self.buffer.write(buf)
        return len(buf)

# Initialisation de la caméra en mode haute performance
def initialize_camera():
    camera = Picamera2()
    camera_config = camera.create_video_configuration(
        main={"size": (frame_width, frame_height), "format": "RGB888"},
        controls={"FrameRate": fps},
        buffer_count=4
    )
    camera.configure(camera_config)
    
    # Configurer l'encodeur JPEG en mémoire
    encoder = JpegEncoder(q=quality)
    output = StreamingOutput()
    camera.start_recording(encoder, FileOutput(output))
    
    return camera, output

# Thread pour capturer les frames
def capture_frames(output):
    global latest_frame
    
    while True:
        with output.condition:
            output.condition.wait()
            # Mettre à jour le frame avec un lock pour éviter les conflits
            with frame_lock:
                latest_frame = output.frame

# Fonction pour générer le flux vidéo
def generate_frames():
    while True:
        # Récupérer le dernier frame disponible
        with frame_lock:
            if latest_frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
                       
        # Contrôle de débit pour réduire la charge CPU
        time.sleep(1/fps)

# Route pour diffuser le flux vidéo
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Page d'accueil
@app.route('/')
def index():
    # Obtenir l'adresse IP
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
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin: 20px; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            .info {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 20px; }}
        </style>
      </head>
      <body>
        <h1>Flux vidéo de la Raspberry Pi</h1>
        <img src="/video_feed" />
        <div class="info">
            <p>URL du flux vidéo: <code>http://{ip}:5000/video_feed</code></p>
            <p>Résolution: {frame_width}x{frame_height} @ {fps} FPS</p>
        </div>
      </body>
    </html>
    """

if __name__ == '__main__':
    # Initialiser la caméra
    camera, output = initialize_camera()
    
    # Démarrer le thread de capture
    capture_thread = threading.Thread(target=capture_frames, args=(output,), daemon=True)
    capture_thread.start()
    
    # Obtenir l'adresse IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = "localhost"
    
    print(f"Serveur démarré sur http://{ip}:5000")
    print(f"Streaming vidéo: {frame_width}x{frame_height} @ {fps} FPS")
    
    # Démarrer le serveur Flask avec des paramètres optimisés
    app.run(host='0.0.0.0', port=5000, threaded=True)
