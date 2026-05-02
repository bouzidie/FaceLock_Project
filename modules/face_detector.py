"""
FaceLock - Détecteur de Visages (InsightFace)
"""
import cv2
import numpy as np
from insightface.app import FaceAnalysis

class FaceDetector:
    def __init__(self, providers=['CPU']):
        """
        Initialise le détecteur de visages avec insightface.
        """
        self.app = FaceAnalysis(providers=providers)
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect_faces(self, frame):
        """
        Détecte les visages et retourne une liste de bounding boxes.
        Returns: list: [(x, y, largeur, hauteur), ...]
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = self.app.get(rgb_frame)
        
        bounding_boxes = []
        for face in faces:
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            x, y, w, h = x1, y1, x2 - x1, y2 - y1
            
            # Marge de sécurité
            margin = 10
            x = max(0, x - margin)
            y = max(0, y - margin)
            h_img, w_img = frame.shape[:2]
            w = min(w_img - x, w + 2 * margin)
            h = min(h_img - y, h + 2 * margin)
            
            bounding_boxes.append((x, y, w, h))
        
        return bounding_boxes

    def get_face_info(self, frame):
        """Retourne les objets face bruts d'insightface."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.app.get(rgb_frame)

    def crop_face(self, frame, bbox):
        """Recadre le visage."""
        x, y, w, h = bbox
        x, y = max(0, int(x)), max(0, int(y))
        h_img, w_img = frame.shape[:2]
        w, h = min(w_img - x, int(w)), min(h_img - y, int(h))
        return frame[y:y+h, x:x+w]

    def close(self):
        """Libère les ressources."""
        pass