"""
FaceLock - Détection de Vivacité (Anti-Spoofing)
Version: 1.0
Fonctionnalités:
    - Détection de clignement des yeux
    - Estimation de la pose de tête
    - Analyse de texture (détection photo/écran)
    - Challenge-Response (mouvements demandés)
"""

import cv2
import numpy as np
import dlib
from scipy.spatial import distance as dist
import time


class LivenessDetector:
    def __init__(self, predictor_path="models/shape_predictor_68_face_landmarks.dat"):
        """
        Initialise le détecteur de vivacité.
        
        Args:
            predictor_path: Chemin vers le modèle de landmarks faciaux dlib
        """
        self.detector = dlib.get_frontal_face_detector()
        
        try:
            self.predictor = dlib.shape_predictor(predictor_path)
            self.predictor_loaded = True
        except:
            print("⚠️  Modèle de landmarks non trouvé. Téléchargez-le depuis:")
            print("   http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
            self.predictor_loaded = False
        
        # Compteurs pour détection de clignement
        self.eye_ar_history = []
        self.blink_detected = False
        self.last_blink_time = 0
        
        # Pose de tête
        self.head_pose_history = []
        
        # Paramètres
        self.EYE_AR_THRESH = 0.3  # Seuil de clignement
        self.EYE_AR_CONSEC_FRAMES = 3  # Frames consécutives
        
        # Indices des landmarks pour les yeux (68 points)
        self.LEFT_EYE = list(range(36, 42))
        self.RIGHT_EYE = list(range(42, 48))

    def eye_aspect_ratio(self, eye_points):
        """Calcule l'Eye Aspect Ratio (EAR) pour détecter le clignement."""
        # Coordonnées des points des yeux
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        C = dist.euclidean(eye_points[0], eye_points[3])
        
        ear = (A + B) / (2.0 * C)
        return ear

    def detect_blink(self, frame):
        """
        Détecte si un clignement d'yeux se produit.
        
        Returns:
            bool: True si clignement détecté
        """
        if not self.predictor_loaded:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)
        
        if len(faces) == 0:
            return False
        
        # Prendre le premier visage
        shape = self.predictor(gray, faces[0])
        shape_points = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
        
        # Extraire les points des yeux
        left_eye = [shape_points[i] for i in self.LEFT_EYE]
        right_eye = [shape_points[i] for i in self.RIGHT_EYE]
        
        # Calculer EAR pour chaque oeil
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Historique
        self.eye_ar_history.append(avg_ear)
        if len(self.eye_ar_history) > self.EYE_AR_CONSEC_FRAMES:
            self.eye_ar_history.pop(0)
        
        # Détecter clignement
        if all(ear < self.EYE_AR_THRESH for ear in self.eye_ar_history):
            current_time = time.time()
            if current_time - self.last_blink_time > 2.0:  # Anti-spam
                self.blink_detected = True
                self.last_blink_time = current_time
                return True
        
        return False

    def estimate_head_pose(self, frame):
        """
        Estime la pose de tête (pitch, yaw, roll).
        
        Returns:
            tuple: (pitch, yaw, roll) en degrés
        """
        if not self.predictor_loaded:
            return (0, 0, 0)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)
        
        if len(faces) == 0:
            return (0, 0, 0)
        
        shape = self.predictor(gray, faces[0])
        
        # Points 3D du modèle
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nez
            (0.0, -330.0, -65.0),        # Menton
            (-225.0, 170.0, -135.0),     # Oeil gauche
            (225.0, 170.0, -135.0),      # Oeil droit
            (-150.0, -150.0, -125.0),    # Bouche gauche
            (150.0, -150.0, -125.0)      # Bouche droite
        ])
        
        # Points 2D correspondants
        h, w = frame.shape[:2]
        image_points = np.array([
            (shape.part(30).x, shape.part(30).y),
            (shape.part(8).x, shape.part(8).y),
            (shape.part(36).x, shape.part(36).y),
            (shape.part(45).x, shape.part(45).y),
            (shape.part(48).x, shape.part(48).y),
            (shape.part(54).x, shape.part(54).y)
        ], dtype=np.double)
        
        # Paramètres de caméra
        focal_length = [w, w]
        center = (w / 2, h / 2)
        camera_matrix = np.array(
            [[focal_length[0], 0, center[0]],
             [0, focal_length[1], center[1]],
             [0, 0, 1]], dtype=np.double
        )
        
        dist_coeffs = np.zeros((4, 1))
        
        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return (0, 0, 0)
        
        # Convertir en angles Euler
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        sy = np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
        
        if sy > 1e-6:
            x = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        else:
            x = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = 0
        
        return (np.degrees(x), np.degrees(y), np.degrees(z))

    def check_texture_quality(self, frame, bbox):
        """
        Analyse la texture pour détecter une photo/écran.
        
        Returns:
            float: Score de qualité de texture (0-1, plus c'est haut, plus c'est réel)
        """
        x, y, w, h = bbox
        face_roi = frame[y:y+h, x:x+w]
        
        if face_roi.size == 0:
            return 0.0
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Calculer la variance de Laplacien (mesure de netteté)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Analyse FFT pour détecter les motifs d'écran
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude_spectrum = np.abs(fft_shift)
        
        # Détecter les pics caractéristiques des écrans (moire pattern)
        high_freq_energy = np.sum(magnitude_spectrum[magnitude_spectrum.shape[0]//4:, 
                                                      magnitude_spectrum.shape[1]//4:])
        
        # Score basé sur la netteté
        sharpness_score = min(1.0, laplacian_var / 500.0)
        
        # Pénaliser les motifs d'écran
        screen_penalty = min(1.0, high_freq_energy / 1e7)
        
        final_score = sharpness_score * (1 - screen_penalty * 0.5)
        
        return final_score

    def challenge_response(self, frame, challenge_type="turn_head"):
        """
        Demande à l'utilisateur d'effectuer un mouvement.
        
        Args:
            challenge_type: "turn_head", "smile", "blink"
            
        Returns:
            bool: True si le défi est réussi
        """
        pitch, yaw, roll = self.estimate_head_pose(frame)
        
        if challenge_type == "turn_head":
            # Demander de tourner la tête
            if abs(yaw) > 20:  # Tête tournée de plus de 20 degrés
                return True
        
        elif challenge_type == "nod":
            # Demander de hocher la tête
            if abs(pitch) > 15:  # Tête inclinée de plus de 15 degrés
                return True
        
        elif challenge_type == "blink":
            if self.detect_blink(frame):
                return True
        
        return False

    def verify_liveness(self, frame, bbox=None, mode="passive"):
        """
        Vérification complète de vivacité.
        
        Args:
            frame: Image OpenCV
            bbox: Bounding box du visage (x, y, w, h)
            mode: "passive" (analyse automatique) ou "active" (challenge-response)
            
        Returns:
            dict: {
                'is_live': bool,
                'score': float (0-1),
                'details': {
                    'blink_detected': bool,
                    'head_pose': tuple,
                    'texture_score': float,
                    'challenge_passed': bool
                }
            }
        """
        if bbox is None:
            # Détection automatique
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray, 0)
            if len(faces) == 0:
                return {
                    'is_live': False,
                    'score': 0.0,
                    'details': {'error': 'No face detected'}
                }
            face = faces[0]
            bbox = (face.left(), face.top(), 
                   face.right() - face.left(), 
                   face.bottom() - face.top())
        
        # Analyses passives
        blink_detected = self.detect_blink(frame)
        head_pose = self.estimate_head_pose(frame)
        texture_score = self.check_texture_quality(frame, bbox)
        
        # Score global
        score = 0.0
        
        # Clignement détecté = +0.3
        if blink_detected:
            score += 0.3
        
        # Texture réaliste = +0.4
        score += texture_score * 0.4
        
        # Mouvement de tête naturel = +0.3
        pitch, yaw, roll = head_pose
        if abs(yaw) > 5 or abs(pitch) > 5:
            score += 0.3
        
        # Mode actif : challenge-response
        challenge_passed = False
        if mode == "active":
            challenge_passed = self.challenge_response(frame, "turn_head")
            if challenge_passed:
                score += 0.2  # Bonus pour challenge réussi
        
        is_live = score > 0.6  # Seuil de décision
        
        return {
            'is_live': is_live,
            'score': min(1.0, score),
            'details': {
                'blink_detected': blink_detected,
                'head_pose': head_pose,
                'texture_score': texture_score,
                'challenge_passed': challenge_passed
            }
        }

    def close(self):
        """Libère les ressources."""
        pass