from ..adapters.openai_client import OpenAIClient

class NLUService:
    def __init__(self):
        self.client = OpenAIClient()

    def classify_intent(self, text: str, lang: str):
        return self.client.classify(text, lang)
