# greensentinel_server.py pour la Raspberry Pi
from flask import Flask, Response, render_template_string
import cv2
import numpy as np
import socket
import time
import threading
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
import datetime

app = Flask(__name__)

# Configuration globale
frame_width = 640
frame_height = 480
fps = 15
quality = 80  # Qualité JPEG (0-100)

# Buffer circulaire pour le dernier frame
latest_frame = None
frame_lock = threading.Lock()
detection_count = 0
last_detection_time = None

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

# Fonction pour simuler une détection (à remplacer par vos vraies détections)
def simulate_detection():
    global detection_count, last_detection_time
    detection_count += 1
    last_detection_time = datetime.datetime.now().strftime("%H:%M:%S")

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

# Page d'accueil avec design attractif
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
    
    # Simuler une détection pour démonstration
    if detection_count == 0:
        simulate_detection()
        
    # HTML template avec design vert et thème GreenSentinel
    template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GreenSentinel - Système de Détection d'Incendies</title>
        <style>
            :root {
                --primary-color: #2e7d32;
                --secondary-color: #43a047;
                --accent-color: #81c784;
                --light-color: #e8f5e9;
                --dark-color: #1b5e20;
                --danger-color: #f44336;
                --warning-color: #ff9800;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background-color: var(--light-color);
                color: #333;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            header {
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 20px 0;
                border-radius: 0 0 20px 20px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                margin-bottom: 20px;
            }
            
            .logo {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 10px;
            }
            
            .logo svg {
                width: 40px;
                height: 40px;
                margin-right: 15px;
                fill: white;
            }
            
            h1 {
                text-align: center;
                font-size: 2.5rem;
                margin: 5px 0;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            }
            
            .tagline {
                text-align: center;
                font-style: italic;
                color: var(--light-color);
                margin-bottom: 10px;
            }
            
            .video-container {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                text-align: center;
            }
            
            .video-feed {
                width: 100%;
                max-width: 800px;
                height: auto;
                border-radius: 10px;
                border: 3px solid var(--primary-color);
            }
            
            .status-panel {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .status-card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .status-card h3 {
                color: var(--primary-color);
                margin-bottom: 15px;
                border-bottom: 2px solid var(--accent-color);
                padding-bottom: 5px;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: auto 1fr;
                gap: 8px 15px;
                align-items: center;
            }
            
            .info-label {
                font-weight: bold;
                color: var(--secondary-color);
            }
            
            .info-value {
                font-family: 'Courier New', monospace;
            }
            
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 5px;
            }
            
            .status-active {
                background-color: #4CAF50;
                box-shadow: 0 0 5px #4CAF50;
            }
            
            .status-warning {
                background-color: var(--warning-color);
                box-shadow: 0 0 5px var(--warning-color);
            }
            
            .status-danger {
                background-color: var(--danger-color);
                box-shadow: 0 0 5px var(--danger-color);
            }
            
            footer {
                background-color: var(--primary-color);
                color: white;
                text-align: center;
                padding: 15px;
                border-radius: 20px 20px 0 0;
                font-size: 0.9rem;
            }
            
            .pulse {
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(46, 125, 50, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(46, 125, 50, 0);
                }
            }
            
            @media (max-width: 768px) {
                h1 {
                    font-size: 1.8rem;
                }
                
                .status-panel {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M12,3c-4.8,0-9,3.86-9,9c0,2.12,0.74,4.07,1.97,5.61L3,19.59L4.41,21l1.97-1.97C7.93,20.26,9.88,21,12,21
                    c2.3,0,4.61-0.88,6.36-2.64C20.12,16.61,21,14.3,21,12c0-2.3-0.88-4.61-2.64-6.36C16.61,3.88,14.3,3,12,3z M12,19
                    c-3.86,0-7-3.14-7-7c0-3.86,3.14-7,7-7c3.86,0,7,3.14,7,7C19,15.86,15.86,19,12,19z"/>
                    <path d="M12.5,7v4.25l3.5,2.08l-0.72,1.21L11,12V7H12.5z"/>
                    <path d="M18,12c0,3.31-2.69,6-6,6s-6-2.69-6-6h2c0,2.21,1.79,4,4,4s4-1.79,4-4s-1.79-4-4-4v2l-3-3l3-3v2
                    C15.31,6,18,8.69,18,12z"/>
                </svg>
                <h1>GreenSentinel</h1>
            </div>
            <p class="tagline">Protection intelligente contre les incendies de forêt</p>
        </header>
        
        <div class="container">
            <div class="video-container pulse">
                <h2>Surveillance en direct</h2>
                <p>Flux vidéo provenant du capteur de la Raspberry Pi</p>
                <br>
                <img src="/video_feed" class="video-feed" alt="Flux vidéo en direct">
            </div>
            
            <div class="status-panel">
                <div class="status-card">
                    <h3>État du système</h3>
                    <div class="info-grid">
                        <span class="info-label">État:</span>
                        <span><span class="status-indicator status-active"></span> Actif</span>
                        
                        <span class="info-label">Résolution:</span>
                        <span class="info-value">{{ width }}x{{ height }} @ {{ fps }} FPS</span>
                        
                        <span class="info-label">URL du flux:</span>
                        <span class="info-value">http://{{ ip }}:5000/video_feed</span>
                        
                        <span class="info-label">Qualité image:</span>
                        <span class="info-value">{{ quality }}%</span>
                    </div>
                </div>
                
                <div class="status-card">
                    <h3>Détection d'incendies</h3>
                    <div class="info-grid">
                        <span class="info-label">Nombre de détections:</span>
                        <span class="info-value">{{ detections }}</span>
                        
                        <span class="info-label">Dernière détection:</span>
                        <span class="info-value">{{ last_detection }}</span>
                        
                        <span class="info-label">État d'alerte:</span>
                        <span><span class="status-indicator {{ 'status-danger' if detections > 0 else 'status-active' }}"></span>
                        {{ 'Alerte active' if detections > 0 else 'Normal' }}</span>
                        
                        <span class="info-label">Modèle IA:</span>
                        <span class="info-value">YOLO (try.pt)</span>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>GreenSentinel &copy; 2025 | Système de détection d'incendies par intelligence artificielle</p>
        </footer>
    </body>
    </html>
    """
    
    return render_template_string(template,
                                  width=frame_width,
                                  height=frame_height,
                                  fps=fps,
                                  ip=ip,
                                  quality=quality,
                                  detections=detection_count,
                                  last_detection=last_detection_time or "Aucune")


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
    
    print(f"GreenSentinel démarré sur http://{ip}:5000")
    print(f"Streaming vidéo: {frame_width}x{frame_height} @ {fps} FPS")
    
    # Démarrer le serveur Flask avec des paramètres optimisés
    app.run(host='0.0.0.0', port=5000, threaded=True)
