import requests
from ..common.config import settings
from ..common.logging import logger

class PerfectGymClient:
    def __init__(self):
        self.base = settings.pg_base_url.rstrip("/") if settings.pg_base_url else ""

    def _headers(self):
        return {
            "X-Client-id": settings.pg_client_id or "",
            "X-Client-Secret": settings.pg_client_secret or "",
            "Content-Type": "application/json"
        }

    def get_member(self, member_id: str):
        if not self.base:
            return {"member_id": member_id, "status": "Current", "balance": 0}
        url = f"{self.base}/Members({member_id})?$expand=Contracts($filter=Status eq 'Current'),memberbalance"
        r = requests.get(url, headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def reserve_class(self, member_id: str, class_id: str, idempotency_key: str):
        if not self.base:
            return {"ok": True, "reservation_id": f"r-{class_id}"}
        url = f"{self.base}/Classes({class_id})/Reserve"
        payload = {"MemberId": member_id}
        headers = self._headers()
        headers["Idempotency-Key"] = idempotency_key
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
