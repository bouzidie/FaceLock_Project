import numpy as np

class FaceAuthenticator:
    def __init__(self, db, threshold=0.4):
        """
        Initialise l'authentificateur.
        
        Args:
            db: Instance de FaceDatabase
            threshold: Seuil de similarité cosinus (0 à 1)
                      Pour ArcFace (512D), un seuil de 0.35-0.45 est recommandé
        """
        self.db = db
        self.threshold = threshold

    def authenticate(self, current_embedding):
        """
        Compare l'embedding actuel avec la base de données.
        
        Args:
            current_embedding: numpy array de shape (512,) pour ArcFace
            
        Returns:
            str: Nom de l'utilisateur si match trouvé, sinon None
        """
        known_users = self.db.get_all_users()
        
        if not known_users or current_embedding is None:
            return None

        best_score = -1
        best_user = None
        
        for user in known_users:
            known_embedding = np.array(user['embedding'], dtype=np.float32)
            
            # Calculer la similarité cosinus
            similarity = self._cosine_similarity(current_embedding, known_embedding)
            
            if similarity > best_score:
                best_score = similarity
                best_user = user['username']
        
        # Vérifier si le meilleur score dépasse le seuil
        if best_score >= self.threshold:
            # print(f"✓ Authentifié: {best_user} (score: {best_score:.3f})")
            return best_user
        
        # print(f"✗ Rejeté: score {best_score:.3f} < seuil {self.threshold}")
        return None

    def _cosine_similarity(self, vec1, vec2):
        """
        Calcule la similarité cosinus entre deux vecteurs.
        Retourne une valeur entre -1 et 1 (1 = identique).
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 * norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def adjust_threshold(self, new_threshold):
        """Permet d'ajuster le seuil dynamiquement."""
        self.threshold = new_threshold
        print(f"Seuil de similarité ajusté à: {new_threshold}")