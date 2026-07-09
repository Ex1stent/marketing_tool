from __future__ import annotations

from core.whatsapp_parse import WhatsappWebhookParser
from core.base_webhook_processor import BaseWebhookProcessor


class WhatsappWebhookProcessor(BaseWebhookProcessor):
    def __init__(self):
        super().__init__()
        self.parse = WhatsappWebhookParser()

    async def process(self, payload: dict):
        return await super().process(payload, self.parse)
