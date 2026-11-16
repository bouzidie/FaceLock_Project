"""
Client Named Pipe - Version Robuste (Gestion d'erreurs Win32)
"""
import win32file
import win32pipe
import pywintypes

class NamedPipeClient:
    def __init__(self, pipe_name: str, timeout: float = 5.0):
        self.pipe_name = pipe_name
        self.timeout = timeout

    def send(self,  bytes) -> bytes:
        handle = None
        try:
            handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            
            win32pipe.SetNamedPipeHandleState(
                handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
            )
            
            win32file.WriteFile(handle, data)
            _, response = win32file.ReadFile(handle, 65536)
            return response

        except pywintypes.error as e:
            if e.winerror == 2:
                raise ConnectionError(f"Pipe introuvable: {self.pipe_name}. Serveur éteint ?")
            elif e.winerror == 109:
                raise ConnectionError("Serveur a fermé le pipe avant de répondre.")
            elif e.winerror == 232:
                raise ConnectionError("Connexion rompue.")
            else:
                raise ConnectionError(f"Win32 {e.winerror}: {e}")
        except Exception as e:
            raise ConnectionError(f"Erreur: {e}")
        finally:
            if handle is not None:
                try: win32file.CloseHandle(handle)
                except: pass