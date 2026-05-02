"""
FaceLock Protocol - Structures de données pour la communication Named Pipe
"""
from dataclasses import dataclass, asdict
from typing import Optional
import json

@dataclass
class AuthRequest:
    """Requête envoyée par le client vers le service"""
    image_base64: str
    timestamp: float

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'AuthRequest':
        return cls(**json.loads(json_str))

@dataclass
class AuthResponse:
    """Réponse envoyée par le service vers le client"""
    status: str  # "success", "rejected", "error"
    username: Optional[str] = None
    reason: Optional[str] = None
    liveness_score: Optional[float] = None
    processing_time: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'AuthResponse':
        return cls(**json.loads(json_str))