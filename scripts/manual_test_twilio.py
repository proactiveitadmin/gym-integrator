from twilio.rest import Client
import os

sid = os.getenv("TWILIO_ACCOUNT_SID")
token = os.getenv("TWILIO_AUTH_TOKEN")
from_nr = os.getenv("TWILIO_WHATSAPP_NUMBER")
to_nr = "whatsapp:+48694757634"

client = Client(sid, token)
msg = client.messages.create(
    from_=from_nr,
    to=to_nr,
    body="TEST bezpośrednio z Twilio"
)
print(msg.sid, msg.status)
