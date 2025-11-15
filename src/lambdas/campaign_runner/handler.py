import os, json
from ...services.campaign_service import CampaignService
from ...common.aws import sqs_client, ddb_resource

OUTBOUND_QUEUE_URL = os.getenv("OutboundQueueUrl")
CAMPAIGNS_TABLE = os.getenv("DDB_TABLE_CAMPAIGNS", "Campaigns")
svc = CampaignService()

def lambda_handler(event, context):
    table = ddb_resource().Table(CAMPAIGNS_TABLE)
    resp = table.scan()
    out_q_url = resolve_queue_url("OutboundQueueName")
    for item in resp.get("Items", []):
        if not item.get("active", False):
            continue
        for phone in item.get("recipients", []):
            body = item.get("body", "Nowa oferta klubu!")
            sqs_client().send_message(QueueUrl=out_q_url, MessageBody=json.dumps({"to": phone, "body": body}))
    return {"statusCode": 200}
