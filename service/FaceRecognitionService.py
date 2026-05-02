"""
FaceLock Windows Service - Version Hybride Finale (Debug + Service)
Copiez-collez TOUT ce code dans service/FaceRecognitionService.py
"""
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import logging
import yaml
import time
import base64
import cv2
from datetime import datetime
import numpy as np

# Ajouter le parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.protocol import AuthRequest, AuthResponse
from modules.named_pipe_server import NamedPipeServer
from modules.face_detector import FaceDetector
from modules.face_encoder import FaceEncoder
from modules.face_authenticator import FaceAuthenticator
from modules.database import FaceDatabase
from modules.liveness_detector import LivenessDetector

# =============================================================================
# LOGIQUE MÉTIER (Indépendante de Windows Service)
# =============================================================================

class FaceLockEngine:
    """Moteur biométrique pur - Peut tourner n'importe où"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("FaceLockEngine")
        self.pipe_server = None
        
    def start(self):
        """Initialise et démarre le moteur"""
        print("Loading models...")
        
        # Initialisation des composants
        self.db = FaceDatabase()
        self.detector = FaceDetector()
        self.encoder = FaceEncoder()
        self.authenticator = FaceAuthenticator(self.db, threshold=self.config['auth']['threshold'])
        
        liveness_model_path = os.path.join(self.config['paths']['models_dir'], 
                                           self.config['paths']['liveness_model'])
        self.liveness = LivenessDetector(predictor_path=liveness_model_path)
        
        print("Models loaded successfully")
        
        # Démarrer le serveur Named Pipe
        self.pipe_server = NamedPipeServer(
            pipe_name=self.config['pipe']['name'],
            handler_callback=self._handle_auth_pipeline,
            buffer_size=self.config['pipe']['buffer_size']
        )
        
        import threading
        pipe_thread = threading.Thread(target=self.pipe_server.start, daemon=True)
        pipe_thread.start()
        
        print("Service ready and waiting on", self.config['pipe']['name'])
        
        # Garder le processus actif
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            if self.pipe_server:
                self.pipe_server.stop()
    
    def _handle_auth_pipeline(self, request_bytes: bytes) -> bytes:
        start_time = time.time()
        ts = datetime.now().strftime('%H:%M:%S')
        try:
            request = AuthRequest.from_json(request_bytes.decode('utf-8'))
            
            img_bytes = base64.b64decode(request.image_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                print(f"[{ts}] ️  Erreur: Image invalide")
                return AuthResponse(status="error", reason="invalid_image").to_json().encode()
            
            faces = self.detector.detect_faces(frame)
            if not faces:
                print(f"[{ts}] 👤 Aucun visage détecté")
                return AuthResponse(status="rejected", reason="no_face").to_json().encode()
            
            liveness_res = self.liveness.verify_liveness(frame, faces[0], mode="passive")
            if not liveness_res['is_live']:
                print(f"[{ts}] ⚠️  SPOOFING DÉTECTÉ (score vivacité: {liveness_res['score']:.2f})")
                return AuthResponse(status="rejected", reason="spoofing", 
                                    liveness_score=liveness_res['score']).to_json().encode()
            
            embedding = self.encoder.get_embedding(frame, faces[0])
            if embedding is None:
                print(f"[{ts}] ❌ Échec de l'encodage facial")
                return AuthResponse(status="error", reason="encoding_failed").to_json().encode()
                
            user = self.authenticator.authenticate(embedding)
            proc_time = time.time() - start_time
            
            if user:
                print(f"[{ts}] ✅ AUTHENTIFIÉ: {user} | Latence: {proc_time:.2f}s")
                return AuthResponse(status="success", username=user, 
                                    liveness_score=liveness_res['score'],
                                    processing_time=proc_time).to_json().encode()
            else:
                print(f"[{ts}] ❌ UTILISATEUR INCONNU")
                return AuthResponse(status="rejected", reason="unknown_user",
                                    liveness_score=liveness_res['score'],
                                    processing_time=proc_time).to_json().encode()
                                    
        except Exception as e:
            print(f"[{ts}] 💥 ERREUR PIPELINE: {e}")
            return AuthResponse(status="error", reason=str(e)).to_json().encode()

# =============================================================================
# WRAPPER SERVICE WINDOWS (Seulement pour l'installation)
# =============================================================================

class FaceLockService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FaceLockService"
    _svc_display_name_ = "FaceLock Biometric Service"
    _svc_description_ = "Service d'authentification biométrique par reconnaissance faciale"
    
    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.engine = None
        self._setup_logging()
        
    def _setup_logging(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            log_cfg = self.config['logging']
            log_dir = os.path.dirname(log_cfg['file'])
            os.makedirs(log_dir, exist_ok=True)
            
            logging.basicConfig(
                level=getattr(logging, log_cfg['level']),
                format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                handlers=[
                    logging.FileHandler(log_cfg['file'], maxBytes=log_cfg['max_bytes'], backupCount=log_cfg['backup_count']),
                    logging.StreamHandler()
                ]
            )
        except Exception as e:
            print(f"Error setting up logging: {e}")

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), self.config['paths']['project_root']))
            os.chdir(project_root)
            
            self.engine = FaceLockEngine(self.config)
            self.engine.start()
            
        except Exception as e:
            print(f"Critical Error: {e}")
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL (VÉRIFIEZ QUE C'EST BIEN ÇÀ À LA FIN DU FICHIER)
# =============================================================================

def run_debug_mode():
    """Lance le moteur en mode console (sans Windows Service)"""
    print("DEBUG MODE STARTED")
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), config['paths']['project_root']))
    os.chdir(project_root)
    print(f"Working directory: {project_root}")
    engine = FaceLockEngine(config)
    engine.start()

if __name__ == '__main__':
    # Mode Debug : on bypass complètement Windows Service
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        run_debug_mode()
    else:
        # Mode Service Windows classique
        win32serviceutil.HandleCommandLine(FaceLockService)