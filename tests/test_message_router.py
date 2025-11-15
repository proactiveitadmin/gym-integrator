import json, boto3
from src.lambdas.message_router.handler import lambda_handler

def test_router_faq_to_outbound(aws_stack, mocker):
    # Twardo wymuszamy, że NLU zwraca FAQ(hours)
    mocker.patch(
        "src.services.nlu_service.NLUService.classify_intent",
        return_value={"intent": "faq", "confidence": 0.9, "slots": {"topic": "hours"}},
    )

    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "event_id": "evt-1",
                        "from": "whatsapp:+48123123123",
                        "to": "whatsapp:+48000000000",
                        "body": "godziny",
                        "tenant_id": "default",
                    }
                )
            }
        ]
    }

    lambda_handler(event, None)

    sqs = boto3.client("sqs", region_name="eu-central-1")
    resp = sqs.receive_message(
        QueueUrl=aws_stack["outbound"],
        MaxNumberOfMessages=10,
        WaitTimeSeconds=0,  # bez long-polla
    )
    messages = resp.get("Messages", [])
    assert messages, "Brak wiadomości na kolejce outbound"

    payloads = [json.loads(m["Body"]) for m in messages]

    faq_msgs = [
        p
        for p in payloads
        if p.get("to") == "whatsapp:+48123123123"
        and ("godzin" in p.get("body", "").lower() or "otwar" in p.get("body", "").lower())
    ]

    assert faq_msgs, (
        "Nie znaleziono odpowiedzi FAQ na 'godziny' w kolejce outbound.\n"
        f"Wiadomości: {[p.get('body') for p in payloads]}"
    )

def test_router_reservation_confirm_flow(aws_stack, mocker):
    mocker.patch("src.services.nlu_service.NLUService.classify_intent", return_value={
        "intent":"reserve_class","confidence":0.9,"slots":{"class_id":"777","member_id":"105"}
    })
    event1 = {"Records":[{"body": json.dumps({
        "event_id":"evt-2","from":"whatsapp:+48123123123","to":"whatsapp:+48000000000","body":"chcę rezerwację","tenant_id":"default"
    })}]}
    lambda_handler(event1, None)

    mocker.patch("src.adapters.perfectgym_client.PerfectGymClient.reserve_class", return_value={"ok": True, "reservation_id":"r-777"})
    event2 = {"Records":[{"body": json.dumps({
        "event_id":"evt-3","from":"whatsapp:+48123123123","to":"whatsapp:+48000000000","body":"TAK","tenant_id":"default"
    })}]}
    lambda_handler(event2, None)

    sqs = boto3.client("sqs", region_name="eu-central-1")
    msgs = sqs.receive_message(QueueUrl=aws_stack["outbound"], MaxNumberOfMessages=10)
    bodies = [json.loads(m["Body"]) for m in msgs.get("Messages", [])]
    assert any("Czy potwierdzasz rezerwację" in b.get("body","") for b in bodies)
    assert any("Zarezerwowano" in b.get("body","") for b in bodies)
