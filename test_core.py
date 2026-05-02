import cv2
import numpy as np
from modules.camera_handler import CameraHandler
from modules.face_detector import FaceDetector
from modules.face_encoder import FaceEncoder

print("🔍 Test du noyau FaceLock avec insightface (ArcFace)...")
print("Appuyez sur 'q' pour quitter, 'c' pour capturer un embedding")

# Initialiser les modules
camera = CameraHandler()
detector = FaceDetector()  # Utilise insightface
encoder = FaceEncoder()    # Utilise ArcFace

if not camera.start():
    print("❌ Échec: Impossible d'ouvrir la caméra")
    exit()

try:
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        
        # Détecter les visages
        faces = detector.detect_faces(frame)
        
        # Dessiner les bounding boxes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Visage detecte", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow('FaceLock - Test Core (insightface)', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c') and faces:
            # Capturer et encoder le premier visage
            embedding = encoder.get_embedding(frame, faces[0])
            if embedding is not None:
                print(f"✅ Embedding capturé !")
                print(f"   Dimensions: {embedding.shape}")  # Doit être (512,)
                print(f"   Premier 10 valeurs: {embedding[:10]}")
                print(f"   Norme du vecteur: {np.linalg.norm(embedding):.3f}")
            else:
                print("❌ Échec de l'encodage")
                
except KeyboardInterrupt:
    print("\n⚠️ Interruption")
finally:
    camera.stop()
    detector.close()
    encoder.close()
    cv2.destroyAllWindows()
    print("✅ Test terminé")