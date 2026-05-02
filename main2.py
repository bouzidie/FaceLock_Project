"""
===============================================================================
FaceLock - Optimisation Automatique du Seuil de Reconnaissance
Version: 1.0 (Phase 5 - Optimisation)
===============================================================================
Description:
    Teste automatiquement plusieurs seuils de similarité et recommande
    le meilleur compromis entre sécurité et confort d'utilisation.
    
Usage:
    python main2.py
===============================================================================
"""

import time
import cv2
import numpy as np
from datetime import datetime
from modules.camera_handler import CameraHandler
from modules.face_detector import FaceDetector
from modules.face_encoder import FaceEncoder
from modules.face_authenticator import FaceAuthenticator
from modules.database import FaceDatabase


# =============================================================================
# CONFIGURATION
# =============================================================================

THRESHOLDS_TO_TEST = [0.30, 0.35, 0.40, 0.45, 0.50]  # Seuils à tester
PHOTOS_PER_THRESHOLD = 5  # Nombre de photos par seuil
CAPTURE_INTERVAL = 1.0  # Secondes entre chaque capture


# =============================================================================
# FONCTIONS D'AFFICHAGE
# =============================================================================

def print_header():
    """Affiche l'en-tête du test."""
    print("\n" + "=" * 80)
    print("🔬 FACELOCK - OPTIMISATION AUTOMATIQUE DU SEUIL DE RECONNAISSANCE")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Seuils testés: {THRESHOLDS_TO_TEST}")
    print(f"📸 Photos par seuil: {PHOTOS_PER_THRESHOLD}")
    print("=" * 80)


def print_threshold_header(threshold):
    """Affiche l'en-tête pour un seuil spécifique."""
    print(f"\n{'='*80}")
    print(f"🧪 TEST DU SEUIL: {threshold}")
    print(f"{'='*80}")


def print_results_table(results):
    """Affiche un tableau des résultats."""
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 80)
    
    # En-têtes
    print(f"{'Seuil':<10} | {'Reconnu':<10} | {'Rejeté':<10} | {'Précision':<10} | {'Statut':<15}")
    print("-" * 80)
    
    # Lignes
    for threshold, recognized, rejected, accuracy in results:
        status = "✅ Bon" if accuracy >= 0.8 else "⚠️ Moyen" if accuracy >= 0.6 else "❌ Mauvais"
        print(f"{threshold:<10} | {recognized:<10} | {rejected:<10} | {accuracy*100:<10.1f}% | {status:<15}")
    
    print("=" * 80)


def print_recommendation(best_threshold, best_accuracy):
    """Affiche la recommandation finale."""
    print("\n" + "=" * 80)
    print("🎯 RECOMMANDATION")
    print("=" * 80)
    print(f"✅ MEILLEUR SEUIL: {best_threshold}")
    print(f"📊 Précision: {best_accuracy*100:.1f}%")
    print(f"\n💡 Pour utiliser ce seuil dans main.py, modifiez la ligne:")
    print(f"   RECOGNITION_THRESHOLD = {best_threshold}")
    print("=" * 80 + "\n")


# =============================================================================
# FONCTION DE TEST
# =============================================================================

def test_threshold(threshold, camera, detector, encoder, db):
    """
    Teste un seuil spécifique.
    
    Returns:
        tuple: (threshold, recognized_count, rejected_count, accuracy)
    """
    print_threshold_header(threshold)
    
    # Récupérer les utilisateurs de la base
    users = db.get_all_users()
    if not users:
        print("❌ ERREUR: Aucun utilisateur dans la base de données !")
        print("💡 Lancez d'abord: python main.py --enroll")
        return None
    
    reference_user = users[0]
    reference_embedding = np.array(reference_user['embedding'])
    
    print(f"👤 Utilisateur de référence: {reference_user['username']}")
    print(f"📸 {PHOTOS_PER_THRESHOLD} photos vont être capturées...")
    print(f"⏱️  Commence dans 3 secondes...")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n📷 CAPTURE EN COURS...\n")
    
    recognized_count = 0
    rejected_count = 0
    
    for i in range(PHOTOS_PER_THRESHOLD):
        frame = camera.get_frame()
        
        if frame is None:
            print(f"   Photo {i+1}/{PHOTOS_PER_THRESHOLD}: ⚠️  Échec de capture")
            rejected_count += 1
            time.sleep(CAPTURE_INTERVAL)
            continue
        
        faces = detector.detect_faces(frame)
        
        if not faces:
            print(f"   Photo {i+1}/{PHOTOS_PER_THRESHOLD}: ⚠️  Aucun visage détecté")
            rejected_count += 1
            time.sleep(CAPTURE_INTERVAL)
            continue
        
        embedding = encoder.get_embedding(frame, faces[0])
        
        if embedding is None:
            print(f"   Photo {i+1}/{PHOTOS_PER_THRESHOLD}: ⚠️  Échec encodage")
            rejected_count += 1
            time.sleep(CAPTURE_INTERVAL)
            continue
        
        # Calculer la similarité cosinus
        similarity = np.dot(reference_embedding, embedding) / (
            np.linalg.norm(reference_embedding) * np.linalg.norm(embedding)
        )
        
        # Décision basée sur le seuil
        is_recognized = similarity >= threshold
        
        if is_recognized:
            recognized_count += 1
            status = "✅ RECONNU"
        else:
            rejected_count += 1
            status = "❌ REJETÉ"
        
        print(f"   Photo {i+1}/{PHOTOS_PER_THRESHOLD}: Similarité = {similarity:.3f} → {status}")
        
        time.sleep(CAPTURE_INTERVAL)
    
    # Calculer la précision
    total = recognized_count + rejected_count
    accuracy = recognized_count / total if total > 0 else 0
    
    print(f"\n📊 RÉSULTATS pour seuil = {threshold}:")
    print(f"   ✅ Reconnaissances correctes: {recognized_count}/{total}")
    print(f"   ❌ Rejets: {rejected_count}/{total}")
    print(f"   📈 Précision: {accuracy*100:.1f}%")
    
    return (threshold, recognized_count, rejected_count, accuracy)


# =============================================================================
# TEST AVEC INTRUS (Optionnel - Sécurité)
# =============================================================================

def test_intruder_detection(camera, detector, encoder, db, threshold):
    """
    Teste la capacité à rejeter un intrus.
    """
    print(f"\n{'='*80}")
    print(f"🔒 TEST DE SÉCURITÉ: Détection d'intrus (Seuil: {threshold})")
    print(f"{'='*80}")
    print("⚠️  Une personne DIFFÉRENTE de l'utilisateur enregistré doit se placer devant la caméra")
    print("⏱️  Commence dans 5 secondes...")
    
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n📷 CAPTURE EN COURS...\n")
    
    intruder_detected_as_user = 0
    intruder_rejected = 0
    
    for i in range(3):
        frame = camera.get_frame()
        
        if frame is None:
            continue
        
        faces = detector.detect_faces(frame)
        
        if not faces:
            print(f"   Intrus {i+1}/3: ⚠️  Aucun visage détecté")
            continue
        
        embedding = encoder.get_embedding(frame, faces[0])
        
        if embedding is None:
            print(f"   Intrus {i+1}/3: ⚠️  Échec encodage")
            continue
        
        # Créer un authentificateur avec le seuil testé
        authenticator = FaceAuthenticator(db, threshold=threshold)
        user = authenticator.authenticate(embedding)
        
        if user:
            intruder_detected_as_user += 1
            print(f"   Intrus {i+1}/3: ❌ FAUX POSITIF (reconnu comme: {user})")
        else:
            intruder_rejected += 1
            print(f"   Intrus {i+1}/3: ✅ CORRECTEMENT REJETÉ")
        
        time.sleep(1)
    
    total = intruder_detected_as_user + intruder_rejected
    security_rate = intruder_rejected / total if total > 0 else 0
    
    print(f"\n🔒 RÉSULTATS SÉCURITÉ:")
    print(f"   ✅ Intrus rejetés: {intruder_rejected}/{total}")
    print(f"   ❌ Faux positifs: {intruder_detected_as_user}/{total}")
    print(f"   🛡️  Taux de sécurité: {security_rate*100:.1f}%")
    
    return security_rate


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """Fonction principale d'optimisation."""
    
    print_header()
    
    # Initialisation des composants
    print("\n⏳ Initialisation des composants...")
    
    try:
        db = FaceDatabase()
        print("   ✅ Base de données")
        
        camera = CameraHandler()
        print("   ✅ Caméra")
        
        detector = FaceDetector()
        print("   ✅ Détecteur (insightface)")
        
        encoder = FaceEncoder()
        print("   ✅ Encodeur (ArcFace 512D)")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        return
    
    # Vérifier qu'il y a des utilisateurs
    users = db.get_all_users()
    if not users:
        print("\n❌ ERREUR: Aucun utilisateur enregistré !")
        print("💡 Lancez d'abord: python main.py --enroll")
        camera.stop()
        detector.close()
        encoder.close()
        return
    
    print(f"\n✅ Utilisateur trouvé: {users[0]['username']}")
    print("=" * 80)
    
    # Instructions
    print("\n📋 INSTRUCTIONS:")
    print("   1. L'utilisateur enregistré (islem) doit se placer devant la caméra")
    print("   2. Rester dans la même position pour tous les tests")
    print("   3. Bon éclairage recommandé")
    print("   4. Après les tests, une option pour tester la sécurité (intrus) sera proposée")
    print("\n⏱️  Les tests commencent dans 5 secondes...")
    
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    if not camera.start():
        print("❌ Erreur: Impossible d'ouvrir la caméra.")
        return
    
    # Tester tous les seuils
    results = []
    
    for threshold in THRESHOLDS_TO_TEST:
        result = test_threshold(threshold, camera, detector, encoder, db)
        if result:
            results.append(result)
        time.sleep(2)  # Pause entre les tests
    
    # Afficher le tableau des résultats
    print_results_table(results)
    
    # Trouver le meilleur seuil
    if results:
        best_result = max(results, key=lambda x: x[3])  # Max par précision
        best_threshold = best_result[0]
        best_accuracy = best_result[3]
        
        print_recommendation(best_threshold, best_accuracy)
    
    # Test de sécurité (optionnel)
    print("\n" + "=" * 80)
    response = input("🔒 Voulez-vous tester la détection d'intrus ? (o/n): ").strip().lower()
    
    if response == 'o' or response == 'oui':
        print(f"\n💡 Test avec le seuil recommandé: {best_threshold}")
        security_rate = test_intruder_detection(camera, detector, encoder, db, best_threshold)
        
        if security_rate >= 0.9:
            print(f"\n🛡️  EXCELLENT: Sécurité très bonne ({security_rate*100:.1f}%)")
        elif security_rate >= 0.7:
            print(f"\n⚠️  MOYEN: Sécurité acceptable ({security_rate*100:.1f}%)")
        else:
            print(f"\n❌ FAIBLE: Sécurité insuffisante ({security_rate*100:.1f}%)")
            print("💡 Conseil: Augmentez le seuil pour plus de sécurité")
    
    # Nettoyage
    print("\n" + "=" * 80)
    print("🛑 Nettoyage...")
    camera.stop()
    detector.close()
    encoder.close()
    print("✅ Terminé")
    print("=" * 80 + "\n")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    main()