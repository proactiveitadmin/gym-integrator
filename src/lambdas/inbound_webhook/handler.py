import os, json, urllib.parse
from ...common.utils import new_id
from ...common.aws import sqs_client
from ...common.aws import resolve_queue_url
from ...common.security import verify_twilio_signature
from ...common.logging import logger

NGROK_HOST_HINTS = (".ngrok-free.app", ".ngrok.io")

def _is_dev() -> bool:
    return os.getenv("DEV_MODE", "false").lower() == "true"

def _build_public_url(event, headers_in) -> str:
    host = headers_in.get("Host", "localhost")
    raw_path = (event.get("requestContext", {}) or {}).get("path") or event.get("path") or "/webhooks/twilio"
    public_base = os.getenv("TWILIO_PUBLIC_URL")
    if public_base:
        base = public_base.split("?")[0]
    else:
        proto = "https" if any(host.endswith(suf) for suf in NGROK_HOST_HINTS) else headers_in.get("X-Forwarded-Proto", "http")
        base = f"{proto}://{host}{raw_path}"

    mv_qs = event.get("multiValueQueryStringParameters")
    qs = event.get("queryStringParameters")
    query = urllib.parse.urlencode(mv_qs, doseq=True) if mv_qs else (urllib.parse.urlencode(qs) if qs else "")
    return f"{base}?{query}" if query else base

def _verify_sig_compat(url, content_for_sig, signature):
    """
    Adapter, by współpracować z istniejącą sygnaturą verify_twilio_signature.
    Spróbuje (url, content, signature). Jeśli funkcja oczekuje dict, a mamy listę par,
    przekonwertuje na dict (utrata duplikatów kluczy – ale zgodnie z Twoją obecną implementacją).
    """
    try:
        return verify_twilio_signature(url, content_for_sig, signature)
    except TypeError:
        # np. verify_twilio_signature(url, params_dict, signature)
        if isinstance(content_for_sig, list):
            params_dict = {k: v for k, v in content_for_sig}
        elif isinstance(content_for_sig, (str, bytes)):
            # nie wiemy czy Twoja funkcja spodziewa się body czy dict – spróbujemy oba warianty
            try:
                params_dict = json.loads(content_for_sig) if content_for_sig else {}
            except Exception:
                params_dict = {}
        else:
            params_dict = content_for_sig or {}
        return verify_twilio_signature(url, params_dict, signature)
        
def lambda_handler(event, context):
    print("DBG InboundWebhookFunction env:", {
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "LOCALSTACK_ENDPOINT": os.getenv("LOCALSTACK_ENDPOINT"),
        "InboundEventsQueueUrl": os.getenv("InboundEventsQueueUrl"),
    })
    try:
        body_raw = event.get("body") or ""
        if event.get("isBase64Encoded"):
            import base64
            body_raw = base64.b64decode(body_raw).decode("utf-8", errors="ignore")

        if len(body_raw) > 8 * 1024:
            return {"statusCode": 413, "body": "Payload too large"}

        headers_in = event.get("headers") or {}
        ctype = (headers_in.get("Content-Type") or headers_in.get("content-type") or "").lower()

        # parse
        if "application/x-www-form-urlencoded" in ctype:
            pairs = urllib.parse.parse_qsl(body_raw, keep_blank_values=True)
            params = dict(pairs)  # wygodne do użycia niżej
            content_for_sig = pairs
            sig_kind = "form"
        else:
            try:
                params = json.loads(body_raw) if body_raw else {}
            except json.JSONDecodeError:
                params = {}
            content_for_sig = body_raw
            sig_kind = "json"

        # dev short-circuit?
        #if _is_dev() and not os.getenv("InboundEventsQueueUrl"):
         #   logger.info({"webhook": "dev_shortcircuit", "from": params.get("From")})
          #  return {"statusCode": 200, "body": "OK"}

        # signature
        if os.getenv("TWILIO_SKIP_SIGNATURE", "false").lower() != "true":
            url = _build_public_url(event, headers_in)
            signature = headers_in.get("X-Twilio-Signature", "")
            if os.getenv("TWILIO_SKIP_SIGNATURE", "false").lower() != "true":
                url = _build_public_url(event, headers_in)  # jak u Ciebie
                if not _verify_sig_compat(url, content_for_sig, signature):
                    return {"statusCode": 403, "body": "Forbidden"}
            else:
                logger.info({"sig": "skipped_dev"})
        else:
            logger.info({"sig": "skipped_dev"})

        msg = {
            "event_id": new_id("evt-"),
            "from": params.get("From"),
            "to": params.get("To"),
            "body": params.get("Body", ""),
            "tenant_id": "default",
            "ts": (event.get("requestContext") or {}).get("requestTimeEpoch"),
            "message_sid": params.get("MessageSid"),
        }
        logger.info({
            "dbg_env": {
                "AWS_ENDPOINT_URL": os.getenv("AWS_ENDPOINT_URL"),
                "InboundEventsQueueUrl": os.getenv("InboundEventsQueueUrl")
            }
        })

        queue_url = resolve_queue_url("InboundEventsQueueUrl")
        if queue_url:
            try:
                is_fifo = queue_url.endswith(".fifo")
                kwargs = {"QueueUrl": queue_url, "MessageBody": json.dumps(msg)}
                if is_fifo:
                    kwargs["MessageGroupId"] = msg["tenant_id"] or "default"
                    kwargs["MessageDeduplicationId"] = msg["event_id"]
                logger.info({"sqs_send_try": {"queue_url": queue_url, "fifo": is_fifo}})
                sqs_client().send_message(**kwargs)
                logger.info({"sqs_send_ok": True})
            except Exception as e:
                raise

        logger.info({"webhook": "ok", "from": params.get("From"), "body": params.get("Body")})
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/xml"
            },
            "body": "<Response></Response>"
        }

    except Exception as e:
        logger.exception({"error": str(e)})
        return {"statusCode": 500, "body": f"Error: {e}"}
