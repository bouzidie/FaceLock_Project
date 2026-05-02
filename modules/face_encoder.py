import numpy as np
import cv2
from insightface.app import FaceAnalysis

class FaceEncoder:
    def __init__(self, providers=['CPU']):
        """
        Initialise l'encodeur avec le modèle ArcFace d'insightface.
        
        Args:
            providers: Liste des providers ONNX ('CPU', 'CUDA', 'CoreML')
        """
        # FaceAnalysis gère à la fois détection ET encodage
        self.app = FaceAnalysis(providers=providers)
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def get_embedding(self, frame, bbox=None):
        """
        Génère un embedding de 512 dimensions (ArcFace) pour un visage.
        
        Note: ArcFace produit des embeddings de 512D (pas 128D comme FaceNet).
        C'est normal et même mieux (plus précis).
        
        Args:
            frame: Image OpenCV (BGR)
            bbox: (x, y, w, h) optionnel - si fourni, on encode ce visage
            
        Returns:
            numpy array de shape (512,) ou None si aucun visage détecté
        """
        # Convertir en RGB pour insightface
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Détecter et encoder en une seule étape
        faces = self.app.get(rgb_frame)
        
        if not faces:
            return None
        
        # Si bbox fournie, trouver le visage le plus proche
        if bbox is not None:
            target_face = self._find_closest_face(faces, bbox, frame.shape)
            if target_face is None:
                return None
            return target_face.embedding
        
        # Sinon, retourner l'embedding du premier visage détecté
        return faces[0].embedding

    def _find_closest_face(self, faces, bbox, frame_shape):
        """Trouve le visage détecté le plus proche de la bbox cible."""
        if not faces:
            return None
        
        target_x, target_y, target_w, target_h = bbox
        target_center = (target_x + target_w // 2, target_y + target_h // 2)
        
        best_face = None
        best_distance = float('inf')
        
        for face in faces:
            bbox_face = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox_face
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            # Distance euclidienne entre les centres
            distance = np.sqrt((center[0] - target_center[0])**2 + 
                             (center[1] - target_center[1])**2)
            
            if distance < best_distance:
                best_distance = distance
                best_face = face
        
        return best_face

    def get_embedding_from_face_info(self, face_info):
        """
        Extrait l'embedding directement depuis un objet face d'insightface.
        
        Args:
            face_info: Objet face retourné par app.get()
            
        Returns:
            numpy array de shape (512,)
        """
        if face_info is None or face_info.embedding is None:
            return None
        return face_info.embedding

    def close(self):
        """Libère les ressources."""
        pass