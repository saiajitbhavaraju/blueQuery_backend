# models/shared_models.py
from typing import List, Dict, Any, Optional

class SimpleMessage:
    """
    A simple data class to structure messages in the conversation history.
    This ensures consistency across all agents.
    """
    def __init__(self, role: str, content: str, data_payload: Optional[List[Dict[str, Any]]] = None):
        self.role = role
        self.content = content
        self.data_payload = data_payload
