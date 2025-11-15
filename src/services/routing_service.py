import time
from ..domain.models import Message, Action
from ..services.nlu_service import NLUService
from ..services.kb_service import KBService
from ..services.template_service import TemplateService
from ..adapters.perfectgym_client import PerfectGymClient
from ..storage.ddb import ConversationsRepo

CONFIRM_WORDS = {"tak", "tak.", "potwierdzam", "ok"}

class RoutingService:
    def __init__(self):
        self.nlu = NLUService()
        self.kb = KBService()
        self.tpl = TemplateService()
        self.pg = PerfectGymClient()
        self.conv = ConversationsRepo()

    def _pending_key(self, phone: str):
        return f"pending#{phone}"

    def handle(self, msg: Message):
        text = (msg.body or "").strip().lower()
        pending = self.conv.get(self._pending_key(msg.from_phone))
        if pending and text in CONFIRM_WORDS:
            class_id = pending.get("class_id")
            member_id = pending.get("member_id")
            idem = pending.get("idempotency_key")
            res = self.pg.reserve_class(member_id=member_id, class_id=class_id, idempotency_key=idem)
            self.conv.delete(self._pending_key(msg.from_phone))
            if (res or {}).get("ok", True):
                return [Action("reply", {"to": msg.from_phone, "body": f"Zarezerwowano zajęcia (ID {class_id}). Do zobaczenia!"})]
            return [Action("reply", {"to": msg.from_phone, "body": "Nie udało się zarezerwować. Spróbuj ponownie później."})]

        nlu = self.nlu.classify_intent(msg.body, lang="pl")
        intent = nlu.get("intent", "clarify")
        slots = nlu.get("slots", {}) or {}

        if intent == "faq":
            topic = slots.get("topic", "hours")
            answer = self.kb.answer(topic, tenant_id=msg.tenant_id) or "Przepraszam, nie mam informacji."
            return [Action("reply", {"to": msg.from_phone, "body": answer})]

        if intent == "reserve_class":
            class_id = slots.get("class_id", "101")
            member_id = slots.get("member_id", "105")
            idem = f"idem-{int(time.time())}-{msg.from_phone}"
            self.conv.put({"pk": self._pending_key(msg.from_phone), "class_id": class_id, "member_id": member_id, "idempotency_key": idem})
            return [Action("reply", {"to": msg.from_phone, "body": "Czy potwierdzasz rezerwację zajęć? Odpowiedz: TAK/NIE"})]

        if intent == "handover":
            return [Action("reply", {"to": msg.from_phone, "body": "Łączę Cię z pracownikiem klubu (wkrótce stałe przepięcie)."})]

        return [Action("reply", {"to": msg.from_phone, "body": "Czy możesz doprecyzować, w czym pomóc?"})]
