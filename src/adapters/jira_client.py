import base64, requests, json
from ..common.config import settings
from ..common.logging import logger

class JiraClient:
    def __init__(self):
        self.url = settings.jira_url.rstrip("/") if settings.jira_url else ""
        self.project = settings.jira_project_key

    def _auth_header(self):
        if ":" in settings.jira_token:
            token = base64.b64encode(settings.jira_token.encode()).decode()
            return {"Authorization": f"Basic {token}"}
        return {}

    def create_ticket(self, summary: str, description: str, tenant_id: str):
        if not self.url:
            logger.info({"jira": "dev", "summary": summary})
            return {"ok": True, "ticket": "JIRA-DEV"}
        endpoint = f"{self.url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project},
                "summary": f"[{tenant_id}] {summary}",
                "description": description,
                "issuetype": {"name": "Task"}
            }
        }
        headers = {"Content-Type": "application/json", **self._auth_header()}
        r = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=10)
        r.raise_for_status()
        data = r.json()
        return {"ok": True, "ticket": data.get("key", "JIRA-UNK")}
