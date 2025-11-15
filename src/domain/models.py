from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Message:
    tenant_id: str
    from_phone: str
    to_phone: str
    body: str
    channel: str = "whatsapp"
    conversation_id: Optional[str] = None

@dataclass
class Action:
    type: str
    payload: Dict
