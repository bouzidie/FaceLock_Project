"""
FaceLock Named Pipe Client - Timeout 5s + Gestion d'erreurs robuste
"""
import win32file
import win32pipe
import pywintypes
import logging
import threading
import queue

class NamedPipeClient:
    def __init__(self, pipe_name: str, timeout: float = 5.0):
        self.pipe_name = pipe_name
        self.timeout = timeout
        self.logger = logging.getLogger("PipeClient")

    def send_request(self, request_bytes: bytes) -> bytes:
        q = queue.Queue()
        
        def _io_operation():
            try:
                handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0, None,
                    win32file.OPEN_EXISTING,
                    0, None
                )
                win32file.WriteFile(handle, request_bytes)
                _, response = win32file.ReadFile(handle, 65536)
                win32file.CloseHandle(handle)
                q.put(response)
            except Exception as e:
                q.put(e)

        t = threading.Thread(target=_io_operation, daemon=True)
        t.start()
        t.join(self.timeout)

        if t.is_alive():
            raise TimeoutError("Le service ne répond pas (timeout)")
        
        result = q.get_nowait()
        if isinstance(result, Exception):
            raise result
        return result