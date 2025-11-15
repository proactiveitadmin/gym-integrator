import json, os
from ...domain.models import Message
from ...services.routing_service import RoutingService
from ...common.aws import sqs_client
from ...common.logging import logger

def lambda_handler(event, context):
    logger.info({"sender": "message_router start"})
    router = RoutingService()  # tworzymy dopiero tutaj
    out_queue = os.getenv("OutboundQueueUrl")
    for r in event.get("Records", []):
        body = r["body"]
        msg_body = json.loads(body) if isinstance(body, str) else body
        logger.info({"sender": "message_router try msg"})
        logger.info({"message_router": "ok", "from": msg_body.get("from"), "body": msg_body.get("body", "")})
        logger.info({"message_router": "ok", "from": msg_body.get("from"), "body": msg_body.get("body")})
        msg = Message(
            tenant_id=msg_body.get("tenant_id", "default"),
            from_phone=msg_body.get("from"),
            to_phone=msg_body.get("to"),
            body=msg_body.get("body", ""),
            conversation_id=msg_body.get("event_id"),
        )       
        actions = router.handle(msg)
        for a in actions:
            if a.type == "reply":
                sqs_client().send_message(QueueUrl=out_queue, MessageBody=json.dumps(a.payload))
    logger.info({"sender": "message_router send"})
    return {"statusCode": 200}
