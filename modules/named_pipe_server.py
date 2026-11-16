"""
Serveur Named Pipe - Version Anti-Crash (Réponse garantie)
"""
import win32pipe
import win32file
import pywintypes
import logging
import time

logger = logging.getLogger(__name__)

class NamedPipeServer:
    def __init__(self, pipe_name: str, handler_callback, buffer_size: int = 4096):
        self.pipe_name = pipe_name if pipe_name.startswith("\\\\.\\pipe\\") else f"\\\\.\\pipe\\{pipe_name}"
        self.handler_callback = handler_callback
        self.buffer_size = buffer_size
        self._running = False

    def start(self):
        self._running = True
        logger.info(f"👂 Serveur Named Pipe démarré sur {self.pipe_name}")
        
        while self._running:
            pipe_handle = None
            try:
                # 1. Créer le pipe
                pipe_handle = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    self.buffer_size,
                    self.buffer_size,
                    0, None
                )
                
                # 2. Attendre connexion
                win32pipe.ConnectNamedPipe(pipe_handle, None)
                
                # 3. Lire requête
                result, data = win32file.ReadFile(pipe_handle, self.buffer_size)
                if not data:
                    continue
                
                # 4. Traiter (TOUT est isolé pour éviter de tuer le pipe)
                response = None
                try:
                    response = self.handler_callback(data)
                except Exception as e:
                    logger.error(f"❌ Erreur IA: {e}")
                    response = b'{"status":"error","reason":"ia_processing_failed"}'
                
                # 5. Envoyer réponse (avec protection anti-crash)
                if response:
                    try:
                        win32file.WriteFile(pipe_handle, response)
                    except pywintypes.error as werr:
                        # Si le client a déjà fermé, on loggue mais on ne crash pas
                        if werr.winerror != 109:
                            logger.error(f"❌ Échec écriture pipe: {werr}")
                            
            except pywintypes.error as e:
                if e.winerror == 109:
                    logger.debug("🔌 Client déconnecté normalement")
                elif e.winerror == 231:
                    time.sleep(0.2)
                else:
                    logger.error(f"❌ Win32 {e.winerror}: {e}")
            except Exception as e:
                logger.error(f"💥 Erreur serveur: {e}")
            finally:
                # 6. Nettoyage propre
                if pipe_handle is not None:
                    try:
                        win32pipe.DisconnectNamedPipe(pipe_handle)
                        win32file.CloseHandle(pipe_handle)
                    except: pass
                time.sleep(0.05)
                
        logger.info("🛑 Serveur arrêté")

    def stop(self):
        self._running = False