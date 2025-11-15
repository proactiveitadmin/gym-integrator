import os, json, time, boto3, botocore
from src.lambdas.outbound_sender.handler import lambda_handler

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
OUT_Q = os.getenv("OutboundQueueUrl", f"{ENDPOINT}/000000000000/outbound-messages")
sqs = boto3.client("sqs", endpoint_url=ENDPOINT)

print(f"[worker_outbound_sender] polling {OUT_Q} (endpoint={ENDPOINT})")
while True:
    try:
        resp = sqs.receive_message(QueueUrl=OUT_Q, MaxNumberOfMessages=5, WaitTimeSeconds=10)
        msgs = resp.get("Messages", [])
        if not msgs:
            continue
        print(f"[worker_outbound_sender] got {len(msgs)} msg(s)")
        # sanity: pokaż zły JSON
        for m in msgs:
            try:
                json.loads(m["Body"])
            except Exception:
                print(f"[worker_outbound_sender] bad JSON: {m['Body']}")
        event = {"Records": [{"body": m["Body"]} for m in msgs]}
        lambda_handler(event, None)
        for m in msgs:
            sqs.delete_message(QueueUrl=OUT_Q, ReceiptHandle=m["ReceiptHandle"])
        print(f"[worker_outbound_sender] sent {len(msgs)} msg(s)")
    except botocore.exceptions.EndpointConnectionError as e:
        print(f"[worker_outbound_sender] endpoint error: {e}; retry in 2s")
        time.sleep(2)
    except Exception as e:
        print(f"[worker_outbound_sender] error: {e}")
        time.sleep(1)
