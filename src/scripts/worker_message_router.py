import os, json, time, boto3, botocore
from src.lambdas.message_router.handler import lambda_handler

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
IN_Q = os.getenv("InboundEventsQueueUrl", f"{ENDPOINT}/000000000000/inbound-events")
sqs = boto3.client("sqs", endpoint_url=ENDPOINT)

print(f"[worker_message_router] polling {IN_Q} (endpoint={ENDPOINT})")
while True:
    try:
        resp = sqs.receive_message(QueueUrl=IN_Q, MaxNumberOfMessages=5, WaitTimeSeconds=10)
        msgs = resp.get("Messages", [])
        if not msgs:
            continue
        print(f"[worker_message_router] got {len(msgs)} msg(s)")
        event = {"Records": [{"body": m["Body"]} for m in msgs]}
        lambda_handler(event, None)
        for m in msgs:
            sqs.delete_message(QueueUrl=IN_Q, ReceiptHandle=m["ReceiptHandle"])
        print(f"[worker_message_router] processed {len(msgs)} msg(s) -> outbound")
    except botocore.exceptions.EndpointConnectionError as e:
        print(f"[worker_message_router] endpoint error: {e}; retry in 2s")
        time.sleep(2)
    except Exception as e:
        print(f"[worker_message_router] error: {e}")
        time.sleep(1)
