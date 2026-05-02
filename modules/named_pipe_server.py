"""
FaceLock Named Pipe Server - Logs optimisés (DEBUG pour connexions)
"""
import win32pipe
import win32file
import pywintypes
import threading
import logging
import time

class NamedPipeServer:
    def __init__(self, pipe_name: str, handler_callback, max_instances: int = 1, buffer_size: int = 65536):
        self.pipe_name = pipe_name
        self.handler = handler_callback
        self.max_instances = max_instances
        self.buffer_size = buffer_size
        self.is_running = False
        self.logger = logging.getLogger("PipeServer")

    def start(self):
        self.is_running = True
        self.logger.info(f"👂 Serveur Named Pipe démarré sur {self.pipe_name}")
        
        while self.is_running:
            try:
                pipe = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                    self.max_instances,
                    self.buffer_size, self.buffer_size, 0,
                    None
                )
                
                self.logger.debug("⏳ En attente de connexion...")
                win32pipe.ConnectNamedPipe(pipe, None)
                self.logger.debug("✅ Client connecté.")  # <-- DEBUG pour éviter le spam
                
                client_thread = threading.Thread(target=self._handle_client, args=(pipe,), daemon=True)
                client_thread.start()
                
            except pywintypes.error as e:
                code = e.args[0]
                if code == 231:  # PIPE_BUSY
                    time.sleep(0.2)
                    continue
                elif code == 997:  # IO_PENDING
                    continue
                else:
                    self.logger.error(f"❌ Erreur pipe: {e}")
                    if not self.is_running: break
            except Exception as e:
                self.logger.error(f"❌ Erreur boucle: {e}")
                break
                
        self.logger.info("🛑 Serveur arrêté.")

    def _handle_client(self, pipe):
        try:
            _, data = win32file.ReadFile(pipe, self.buffer_size)
            response_bytes = self.handler(data)
            win32file.WriteFile(pipe, response_bytes)
        except Exception as e:
            self.logger.error(f"️ Erreur client: {e}")
        finally:
            try: win32file.CloseHandle(pipe)
            except: pass

    def stop(self):
        self.is_running = False