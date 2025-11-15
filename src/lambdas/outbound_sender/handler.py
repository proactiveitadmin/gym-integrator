import json
from ...adapters.twilio_client import TwilioClient
from ...common.logging import logger

twilio = TwilioClient()

def lambda_handler(event, context):
    records = event.get("Records", [])
    if not records:
        logger.info({"sender": "no_records"})
        return {"statusCode": 200, "body": "no-records"}

    for r in records:
        raw = r.get("body", "")
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except Exception as e:
            logger.error({"sender": "bad_json", "err": str(e), "raw": raw})
            continue

        to = payload.get("to")
        text = payload.get("body")
        if not to or not text:
            logger.warning({"sender": "invalid_payload", "payload": payload})
            continue

        try:
            res = twilio.send_text(to=to, body=text)
            logger.info({"sender": "sent", "to": to, "body": text, "result": res})
        except Exception as e:
            logger.error({"sender": "twilio_fail", "err": str(e), "to": to})

    return {"statusCode": 200}
