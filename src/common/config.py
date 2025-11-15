import os
from dataclasses import dataclass

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@dataclass
class Settings:
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    tenant_default_lang: str = os.getenv("TENANT_DEFAULT_LANG", "pl")

    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_messaging_sid: str = os.getenv("TWILIO_MESSAGING_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_number: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    pg_base_url: str = os.getenv("PG_BASE_URL", "")
    pg_client_id: str = os.getenv("PG_CLIENT_ID", "")
    pg_client_secret: str = os.getenv("PG_CLIENT_SECRET", "")

    jira_url: str = os.getenv("JIRA_URL", "")
    jira_token: str = os.getenv("JIRA_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "GI")

settings = Settings()
