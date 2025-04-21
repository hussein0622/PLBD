from ultralytics import YOLO
model=YOLO("try.pt")  # Load a pretrained YOLOv8 model
model.predict(source="0",  # Use webcam as input source
              conf=0.6,  # Confidence threshold for predictions
              show=True,  # Display the output in a window
)
