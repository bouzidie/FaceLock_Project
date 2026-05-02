from modules.database import FaceDatabase

db = FaceDatabase()
users = db.get_all_users()

print("=" * 50)
print("📋 UTILISATEURS ENREGISTRÉS")
print("=" * 50)

if not users:
    print("Aucun utilisateur enregistré")
else:
    for user in users:
        print(f"✅ Nom: {user['username']}")
        print(f"   Embedding: {len(user['embedding'])} dimensions")
        print(f"   Premières valeurs: {user['embedding'][:5]}")
        print()

print("=" * 50)