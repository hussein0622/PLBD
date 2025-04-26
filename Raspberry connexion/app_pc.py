# client.py pour le PC utilisant Ultralytics YOLO
import cv2
import numpy as np
import requests
import time
from threading import Thread
import argparse
from ultralytics import YOLO

# Argument pour l'adresse IP de la Raspberry Pi
parser = argparse.ArgumentParser(description='Client de détection d\'incendies avec Ultralytics YOLO')
parser.add_argument('--ip', type=str, default='172.22.2.178', 
                   help='Adresse IP de la Raspberry Pi')
parser.add_argument('--port', type=str, default='5000',
                   help='Port du serveur Flask sur la Raspberry Pi')
parser.add_argument('--conf', type=float, default=0.6,
                   help='Seuil de confiance pour les prédictions')
args = parser.parse_args()

# URL du flux vidéo de la Raspberry Pi
url = f'http://{args.ip}:{args.port}/video_feed'

# Charger le modèle YOLOv8 pour la détection d'incendies
print("Chargement du modèle de détection d'incendies...")
model = YOLO("try.pt")  # Chargement du modèle YOLOv8 préentraîné

# Classe pour gérer le flux vidéo en streaming
class VideoStreamingClient:
    def __init__(self, url):
        self.url = url
        self.bytes = bytes()
        self.frame = None
        self.stopped = False
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()
    
    def update(self):
        try:
            r = requests.get(self.url, stream=True)
            if r.status_code != 200:
                print(f"Erreur de connexion: {r.status_code}")
                self.stopped = True
                return
                
            for chunk in r.iter_content(chunk_size=1024):
                self.bytes += chunk
                a = self.bytes.find(b'\xff\xd8')
                b = self.bytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = self.bytes[a:b+2]
                    self.bytes = self.bytes[b+2:]
                    self.frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if self.stopped:
                    break
        except Exception as e:
            print(f"Erreur lors de la récupération du flux vidéo: {e}")
            self.stopped = True
    
    def read(self):
        return self.frame
    
    def stop(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join()

# Fonction principale
def main():
    # Créer l'instance du client de streaming vidéo
    print(f"Connexion au flux vidéo: {url}")
    client = VideoStreamingClient(url)
    
    # Attendre que la connexion soit établie
    time.sleep(2)
    
    try:
        while not client.stopped:
            # Récupérer le frame actuel
            frame = client.read()
            
            # Si un frame est disponible, détecter les incendies
            if frame is not None:
                # Détecter les incendies avec YOLO
                results = model.predict(source=frame, conf=args.conf, verbose=False)
                
                # Dessiner les résultats sur le frame
                annotated_frame = results[0].plot()
                
                # Afficher le résultat
                cv2.imshow('Détection d\'incendies', annotated_frame)
                
                # Quitter si la touche 'q' est pressée
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("Arrêt du client...")
    finally:
        # Nettoyer
        client.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
