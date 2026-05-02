"""
FaceLock - Authentification Faciale pour Windows
Version: 3.0 (Avec Détection de Vivacité / Anti-Spoofing)
"""

import time
import cv2
import argparse
import sys
from datetime import datetime
from tkinter import messagebox, Tk
import winsound

from modules.camera_handler import CameraHandler
from modules.face_detector import FaceDetector
from modules.face_encoder import FaceEncoder
from modules.face_authenticator import FaceAuthenticator
from modules.system_controller import SystemController
from modules.database import FaceDatabase
from modules.liveness_detector import LivenessDetector  # <--- NOUVEAU
from gui.enrollment_gui import EnrollmentGUI


# =============================================================================
# CONFIGURATION
# =============================================================================

LOCK_TIMEOUT = 10
RECOGNITION_THRESHOLD = 0.4
DISPLAY_INFO = True
SHOW_VIDEO = True


# =============================================================================
# FONCTION POUR AFFICHER UN POPUP
# =============================================================================

def show_recognition_popup(username):
    """Affiche une fenêtre popup quand un utilisateur est reconnu."""
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except:
        pass
    
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    messagebox.showinfo(
        "🔐 FaceLock - Authentification",
        f"✅ Utilisateur reconnu : {username}\n\n"
        f"Bienvenue !\n"
        f"Heure: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    root.destroy()


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="FaceLock - Authentification Faciale")
    parser.add_argument("--enroll", action="store_true", help="Mode enrôlement")
    parser.add_argument("--threshold", type=float, default=RECOGNITION_THRESHOLD)
    args = parser.parse_args()

    print("=" * 70)
    print(" FACELOCK - Authentification Faciale pour Windows")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Python: {sys.version.split()[0]}")
    print("=" * 70)
    
    try:
        print("⏳ Initialisation...")
        
        db = FaceDatabase()
        print("   ✅ Base de données")
        
        camera = CameraHandler()
        print("   ✅ Caméra")
        
        detector = FaceDetector()
        print("   ✅ Détecteur (insightface)")
        
        encoder = FaceEncoder()
        print("   ✅ Encodeur (ArcFace 512D)")
        
        authenticator = FaceAuthenticator(db, threshold=args.threshold)
        print(f"   ✅ Authentificateur (seuil: {args.threshold})")
        
        system = SystemController()
        print("   ✅ Contrôleur système")
        
        # <--- NOUVEAU: Initialisation du détecteur de vivacité
        # Assurez-vous d'avoir le fichier models/shape_predictor_68_face_landmarks.dat
        liveness = LivenessDetector(predictor_path="models/shape_predictor_68_face_landmarks.dat")
        print("   ✅ Détecteur de vivacité (Anti-Spoofing)")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        print("💡 Avez-vous installé dlib et scipy ? (pip install dlib scipy)")
        return

    if args.enroll:
        print("\n📝 Mode enrôlement...")
        try:
            EnrollmentGUI(camera, detector, encoder, db)
        except Exception as e:
            print(f"❌ Erreur: {e}")
        finally:
            cleanup(camera, detector, encoder)
        return

    # MODE AUTHENTIFICATION
    print("\n🚀 Mode authentification...")
    print(f"⏱️  Verrouillage: {LOCK_TIMEOUT}s")
    print(f"🎯 Seuil: {args.threshold}")
    print("=" * 70)
    print("💡 Appuyez sur 'q' pour quitter")
    print("=" * 70)
    
    if not camera.start():
        print("❌ Erreur: Impossible d'ouvrir la caméra.")
        return

    users = db.get_all_users()
    if not users:
        print("⚠️  Aucun utilisateur enregistré !")
        print("💡  Lancez: python main.py --enroll")
        print("=" * 70)

    last_seen_time = time.time()
    last_recognition_time = 0
    last_popup_time = 0
    recognition_cooldown = 2
    popup_cooldown = 10
    is_locked = False
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            frame_count += 1
            faces = detector.detect_faces(frame)
            current_time = time.time()

            if faces:
                # Dessiner les rectangles
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Reconnaissance
                if current_time - last_recognition_time >= recognition_cooldown:
                    
                    # =================================================================
                    # NOUVEAU: VÉRIFICATION DE VIVACITÉ (Anti-Spoofing)
                    # =================================================================
                    liveness_res = liveness.verify_liveness(frame, faces[0], mode="passive")
                    
                    if not liveness_res['is_live']:
                        # SPOOFING DÉTECTÉ (Photo, Vidéo, Masque)
                        status_msg = "️ SPOOFING (Pas humain)"
                        status_color = (0, 0, 255)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ SPOOFING: Score={liveness_res['score']:.2f}")
                        
                        # Reset cooldown pour réessayer dans 2s
                        last_recognition_time = current_time
                        
                    else:
                        # VIVACITÉ CONFIRMÉE → On procède à l'authentification
                        embedding = encoder.get_embedding(frame, faces[0])
                        
                        if embedding is not None:
                            user = authenticator.authenticate(embedding)
                            
                            if user:
                                last_seen_time = current_time
                                last_recognition_time = current_time
                                system.prevent_sleep()
                                is_locked = False
                                
                                if current_time - last_popup_time >= popup_cooldown:
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ RECONNU: {user}")
                                    show_recognition_popup(user)
                                    last_popup_time = current_time
                                
                                status_msg = f"✅ {user}"
                                status_color = (0, 255, 0)
                            else:
                                last_recognition_time = current_time
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Inconnu")
                                status_msg = "❌ Inconnu"
                                status_color = (0, 0, 255)
                        else:
                            status_msg = "️  Encodage échoué"
                            status_color = (0, 165, 255)
            else:
                status_msg = "👤 Aucun visage"
                status_color = (128, 128, 128)

            # Verrouillage
            elapsed = current_time - last_seen_time
            
            if elapsed > LOCK_TIMEOUT and not is_locked:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Absence ({elapsed:.1f}s)")
                print(" Verrouillage...")
                system.lock_session()
                is_locked = True
                last_seen_time = current_time
                status_msg = " VERROUILLÉ"
                status_color = (0, 0, 255)

            # Affichage vidéo
            if SHOW_VIDEO:
                try:
                    cv2.putText(frame, status_msg, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
                    
                    fps = frame_count / (current_time - start_time) if current_time > start_time else 0
                    info_text = f"FPS: {fps:.1f} | Utilisateurs: {len(users)}"
                    cv2.putText(frame, info_text, (10, frame.shape[0] - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    
                    cv2.imshow('FaceLock - Authentification', frame)
                except Exception as e:
                    print(f"⚠️  Erreur affichage: {e}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n⚠️  Sortie")
                break

    except KeyboardInterrupt:
        print("\n⚠️  Interruption")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    finally:
        print("\n" + "=" * 70)
        print(" Arrêt...")
        cleanup(camera, detector, encoder)
        print("✅ Arrêté")
        print("=" * 70)


def cleanup(camera, detector, encoder):
    try:
        if camera:
            camera.stop()
            print("   ✅ Caméra fermée")
        
        if detector and hasattr(detector, 'close'):
            detector.close()
            print("   ✅ Détecteur fermé")
        
        if encoder and hasattr(encoder, 'close'):
            encoder.close()
            print("   ✅ Encodeur fermé")
        
        cv2.destroyAllWindows()
        print("   ✅ Fenêtres fermées")
        
    except Exception as e:
        print(f"⚠️  Nettoyage: {e}")


if __name__ == "__main__":
    main()