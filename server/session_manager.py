import threading
from typing import Dict, Any, Optional
import time
from fastapi import HTTPException

# In-memory store
class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.ttl = 3600  # 1 hour

    def create(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._sessions[session_id] = {
                **data,
                "created_at": time.time(),
                "last_active": time.time()
            }

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session_data = self._sessions.get(session_id)
            if not session_data:
                return None
            if time.time() - session_data["last_active"] > self.ttl:
                del self._sessions[session_id]
                return None
            session_data["last_active"] = time.time()
            return session_data

    def get_or_404(self, session_id: str) -> Dict[str, Any]:
        data = self.get(session_id)
        if not data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        return data

    def update(self, session_id: str, updates: Dict[str, Any]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(updates)
                self._sessions[session_id]["last_active"] = time.time()

    def remove(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

session_manager = SessionManager()
