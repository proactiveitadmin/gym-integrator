import json
from botocore.exceptions import ClientError
from ..common.logging import logger
from ..domain.templates import DEFAULT_FAQ
from ..common.aws import s3_client
from ..common.config import settings

class KBService:
    def __init__(self):
        self.bucket = getattr(settings, "KB_BUCKET", "") or ""

    def answer(self, topic: str, tenant_id: str):
        key = f"kb/{tenant_id}/faq.json"
        if not self.bucket:
            return DEFAULT_FAQ.get(topic)
        try:
            obj = s3_client().get_object(Bucket=self.bucket, Key=key)
            data = json.loads(obj["Body"].read())
            return data.get(topic) or DEFAULT_FAQ.get(topic)
        except ClientError:
            logger.info({"kb":"miss","key":key})
            return DEFAULT_FAQ.get(topic)
