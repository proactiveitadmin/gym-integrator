import os, hmac, hashlib, base64
from typing import Dict
from .config import settings

def verify_twilio_signature(url: str, params: Dict[str, str], signature: str) -> bool:
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true" or settings.dev_mode
    if dev_mode:
        return True
    if not settings.twilio_auth_token:
        return False
    s = url + "".join([k + params[k] for k in sorted(params.keys())])
    mac = hmac.new(settings.twilio_auth_token.encode(), s.encode(), hashlib.sha1)
    computed = base64.b64encode(mac.digest()).decode()
    return hmac.compare_digest(computed, signature)
