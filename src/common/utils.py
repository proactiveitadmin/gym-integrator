import json, uuid
from typing import Any

def to_json(o: Any) -> str:
    return json.dumps(o, ensure_ascii=False, separators=(",", ":"))

def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}"
