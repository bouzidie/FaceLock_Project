"""
FaceLock - Gestion de la Base de Données
Version: 2.1 (CHIFFREMENT CORRIGÉ - Sans double encodage)
"""

import sqlite3
import json
import os
from cryptography.fernet import Fernet


class FaceDatabase:
    def __init__(self, db_path='data/facelock.db', encrypt=True):
        """
        Initialise la base de données.
        
        Args:
            db_path: Chemin vers la base de données SQLite
            encrypt: Activer/désactiver le chiffrement (True par défaut)
        """
        self.db_path = db_path
        self.encrypt = encrypt
        
        # Créer le dossier data s'il n'existe pas
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if encrypt:
            # Générer ou charger la clé de chiffrement
            self.key = self._load_or_create_key()
            self.cipher = Fernet(self.key)
            print(f"🔐 Chiffrement activé (clé: {self.key[:20].decode()}...)")
        else:
            self.key = None
            self.cipher = None
            print("⚠️  Chiffrement DÉSACTIVÉ (mode non sécurisé)")
        
        self._init_db()

    def _load_or_create_key(self):
        """
        Charge la clé de chiffrement existante ou en crée une nouvelle.
        """
        key_file = 'data/secret.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
            print(f"🔑 Clé chargée depuis {key_file}")
            return key
        else:
            key = Fernet.generate_key()
            
            os.makedirs('data', exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            
            os.chmod(key_file, 0o600)
            
            print(f"✅ Nouvelle clé générée dans {key_file}")
            print(f"⚠️  CONSERVEZ CE FICHIER EN SÉCURITÉ !")
            
            return key

    def _encrypt_data(self, data):
        """
        Chiffre une chaîne de caractères.
        Fernet retourne déjà des bytes encodés, pas besoin de base64 supplémentaire.
        """
        if not self.encrypt:
            return data
        
        # Chiffrer les données (Fernet retourne des bytes)
        encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
        
        # Convertir bytes → string hexadécimal pour stockage SQLite
        return encrypted_bytes.hex()

    def _decrypt_data(self, encrypted_data):
        """
        Déchiffre une chaîne de caractères.
        """
        if not self.encrypt:
            return encrypted_data
        
        try:
            # Convertir hex → bytes
            encrypted_bytes = bytes.fromhex(encrypted_data)
            
            # Déchiffrer
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"❌ Erreur de déchiffrement: {e}")
            return None

    def _init_db(self):
        """Initialise la base de données."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Base de données initialisée: {self.db_path}")

    def add_user(self, username, embedding):
        """Ajoute un utilisateur chiffré."""
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        embedding_json = json.dumps(embedding_list)
        
        # CHIFFRER l'embedding
        embedding_encrypted = self._encrypt_data(embedding_json)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (username, embedding) VALUES (?, ?)',
                (username, embedding_encrypted)
            )
            conn.commit()
            print(f"✅ Utilisateur '{username}' ajouté (chiffré)")
            return True
        except sqlite3.IntegrityError:
            print(f"❌ L'utilisateur '{username}' existe déjà")
            return False
        finally:
            conn.close()

    def get_user(self, username):
        """Récupère un utilisateur."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT username, embedding FROM users WHERE username = ?',
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        # DÉCHIFFRER l'embedding
        embedding_decrypted = self._decrypt_data(row[1])
        
        if embedding_decrypted is None:
            return None
        
        return {
            'username': row[0],
            'embedding': json.loads(embedding_decrypted)
        }

    def get_all_users(self):
        """Récupère tous les utilisateurs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, embedding FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            embedding_decrypted = self._decrypt_data(row[1])
            
            if embedding_decrypted is not None:
                users.append({
                    'username': row[0],
                    'embedding': json.loads(embedding_decrypted)
                })
        
        return users

    def delete_user(self, username):
        """Supprime un utilisateur (Droit à l'oubli RGPD)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        if deleted:
            print(f"✅ Utilisateur '{username}' supprimé")
        else:
            print(f"⚠️  Utilisateur '{username}' n'existe pas")
        
        return deleted

    def get_user_count(self):
        """Nombre d'utilisateurs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

    def verify_integrity(self):
        """Vérifie l'intégrité."""
        try:
            users = self.get_all_users()
            print(f"✅ Intégrité vérifiée: {len(users)} utilisateur(s)")
            return True
        except Exception as e:
            print(f"❌ Problème d'intégrité: {e}")
            return False

    def backup_database(self, backup_path='data/facelock_backup.db'):
        """Sauvegarde de la base."""
        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"💾 Sauvegarde créée: {backup_path}")