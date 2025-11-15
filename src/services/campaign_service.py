from typing import List, Dict
from ..common.logging import logger
class CampaignService:
    def select_recipients(self, campaign: Dict) -> List[str]:
        recipients = campaign.get("recipients", [])
        logger.info({"campaign": "recipients", "count": len(recipients)})
        return recipients
# TODO Etap 2: add advanced TargetingService
