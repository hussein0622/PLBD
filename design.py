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
        <title>🔥 Détection d'Incendie - Raspberry Pi 🔥</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #FF6B6B, #FFD93D);
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }}
            .card {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0px 10px 25px rgba(0,0,0,0.2);
                text-align: center;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .ip-address {{
                margin-top: 10px;
                font-size: 1.2em;
                color: #555;
            }}
            button {{
                margin-top: 15px;
                padding: 10px 20px;
                background-color: #ff6b6b;
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 1em;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }}
            button:hover {{
                background-color: #e05a5a;
            }}
            img {{
                width: 640px;
                height: 480px;
                border-radius: 10px;
                border: 2px solid #ff6b6b;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎥 Surveillance en Direct</h1>
            <img src="/video_feed" id="videoStream"/>
            <div class="ip-address">Flux disponible sur : <br><b>http://{ip}:5000/video_feed</b></div>
            <button onclick="refreshStream()">Rafraîchir</button>
        </div>

        <script>
            function refreshStream() {{
                var img = document.getElementById('videoStream');
                img.src = '/video_feed?' + new Date().getTime();
            }}
        </script>
    </body>
    </html>
    """
