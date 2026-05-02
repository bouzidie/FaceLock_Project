"""
FaceLock Client - Machine à états stable (Anti-verrouillage intempestif)
"""
import cv2
import time
import base64
import logging
import threading
from datetime import datetime
from tkinter import messagebox, Tk

from modules.camera_handler import CameraHandler
from modules.system_controller import SystemController
from modules.named_pipe_client import NamedPipeClient
from modules.protocol import AuthRequest, AuthResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("FaceLockClient")

PIPE_NAME = r"\\.\pipe\FaceLockPipe"
LOCK_TIMEOUT = 10
STARTUP_GRACE = 6.0  # Période de grâce au démarrage (warmup IA)

def show_popup_async(username):
    def _show():
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showinfo("🔐 FaceLock", f"✅ Bienvenue {username} !\nSession déverrouillée.")
        root.destroy()
    threading.Thread(target=_show, daemon=True).start()

def main():
    logger.info("🚀 Démarrage Client FaceLock")
    camera = CameraHandler()
    system = SystemController()
    client = NamedPipeClient(PIPE_NAME, timeout=5.0)
    
    if not camera.start():
        logger.error("❌ Impossible d'ouvrir la caméra")
        return

    # --- Machine à états ---
    session_start = time.time()
    last_success_time = time.time()
    is_locked = False
    fail_count = 0
    MAX_FAIL_BEFORE_LOCK = 3
    check_interval = 2.0
    last_check = 0
    
    current_status = "Initialisation..."
    status_color = (128, 128, 128)
    
    logger.info(f"📡 Connexion au service: {PIPE_NAME}")

    while True:
        frame = camera.get_frame()
        if frame is None: continue

        now = time.time()
        
        if now - last_check > check_interval:
            last_check = now
            try:
                _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                b64 = base64.b64encode(buf).decode('utf-8')
                req = AuthRequest(image_base64=b64, timestamp=now)
                
                resp_bytes = client.send_request(req.to_json().encode('utf-8'))
                resp = AuthResponse.from_json(resp_bytes.decode('utf-8'))
                
                if resp.status == "success":
                    current_status = f"✅ {resp.username}"
                    status_color = (0, 255, 0)
                    last_success_time = now
                    fail_count = 0  # Reset échecs
                    is_locked = False
                    
                    if fail_count == 0:  # Affiche popup seulement à la 1ère réussite consécutive
                        show_popup_async(resp.username)
                        
                elif resp.status == "rejected":
                    fail_count += 1
                    if resp.reason == "spoofing":
                        current_status = "️ SPOOFING DÉTECTÉ"
                        status_color = (0, 0, 255)
                    else:
                        current_status = "❌ Visage inconnu"
                        status_color = (0, 0, 255)
                else:
                    fail_count += 1
                    current_status = "️ Service HS"
                    status_color = (0, 165, 255)
                    
            except TimeoutError:
                fail_count += 1
                current_status = "⏳ Service lent..."
                status_color = (0, 165, 255)
            except Exception as e:
                fail_count += 1
                current_status = "️ Erreur Comm"
                status_color = (0, 165, 255)
                logger.debug(f"Erreur: {e}")

        # 🔒 Logique de verrouillage robuste
        is_in_grace_period = (now - session_start) < STARTUP_GRACE
        should_lock = (fail_count >= MAX_FAIL_BEFORE_LOCK) and not is_locked and not is_in_grace_period
        
        if should_lock:
            logger.warning("🔒 Verrouillage session (échecs consécutifs)")
            system.lock_session()
            is_locked = True
            current_status = " VERROUILLÉ"
            status_color = (0, 0, 255)
        elif not should_lock and is_locked:
            is_locked = False  # Déverrouillage automatique si la situation s'améliore

        # Affichage
        cv2.putText(frame, current_status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        cv2.imshow('FaceLock Client', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.stop()
    cv2.destroyAllWindows()
    logger.info("👋 Client arrêté")

if __name__ == "__main__":
    main()