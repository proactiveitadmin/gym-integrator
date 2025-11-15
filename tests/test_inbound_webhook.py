from src.lambdas.inbound_webhook.handler import lambda_handler

def test_inbound_pushes_to_sqs(aws_stack):
    event = {
        "headers": {"Host": "localhost"},
        "requestContext": {"path": "/webhooks/twilio", "requestTimeEpoch": 0},
        "body": "From=whatsapp%3A%2B48123123123&To=whatsapp%3A%2B48000000000&Body=godziny",
    }
    res = lambda_handler(event, None)
    assert res["statusCode"] == 200
