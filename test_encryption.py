"""
Test du chiffrement de la base de données
"""
import os

from modules.database import FaceDatabase
import numpy as np

print("=" * 70)
print("🔐 TEST DU CHIFFREMENT DE LA BASE DE DONNÉES")
print("=" * 70)

# Créer une base de données avec chiffrement
db = FaceDatabase(encrypt=True)

# Créer un embedding test
test_embedding = np.random.rand(512).astype(np.float32)

print("\n📊 TEST 1: Ajout d'un utilisateur chiffré")
success = db.add_user("test_user", test_embedding)
print(f"   Résultat: {'✅ Succès' if success else '❌ Échec'}")

print("\n📊 TEST 2: Récupération de l'utilisateur")
user = db.get_user("test_user")
if user:
    print(f"   ✅ Utilisateur trouvé: {user['username']}")
    print(f"   ✅ Embedding déchiffré: {len(user['embedding'])} dimensions")
    
    # Vérifier que l'embedding est correct
    if np.allclose(user['embedding'], test_embedding):
        print(f"   ✅ Embedding CORRECT (chiffrement/déchiffrement OK)")
    else:
        print(f"   ❌ Embedding INCORRECT")
else:
    print("   ❌ Utilisateur non trouvé")

print("\n📊 TEST 3: Liste de tous les utilisateurs")
users = db.get_all_users()
print(f"   ✅ {len(users)} utilisateur(s) trouvé(s)")

print("\n📊 TEST 4: Vérification de l'intégrité")
db.verify_integrity()

print("\n📊 TEST 5: Suppression de l'utilisateur")
db.delete_user("test_user")

print("\n" + "=" * 70)
print("✅ TESTS TERMINÉS")
print("=" * 70)

# Afficher les fichiers créés
print("\n📁 FICHIERS CRÉÉS:")
if os.path.exists('data/secret.key'):
    print("   ✅ data/secret.key (clé de chiffrement)")
if os.path.exists('data/facelock.db'):
    print("   ✅ data/facelock.db (base de données chiffrée)")