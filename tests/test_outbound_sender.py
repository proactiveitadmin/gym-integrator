import json
from src.lambdas.outbound_sender.handler import lambda_handler

def test_outbound_sender_dev_mode():
    event = {"Records":[{"body": json.dumps({"to":"whatsapp:+48123","body":"Hej!"})}]}
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
