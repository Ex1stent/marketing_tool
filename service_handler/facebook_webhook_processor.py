from __future__ import annotations

from core.base_webhook_processor import BaseWebhookProcessor
from core.facebook_parse import FacebookWebhookParser


class FacebookWebhookProcessor(BaseWebhookProcessor):
    def __init__(self):
        super().__init__()
        self.parse = FacebookWebhookParser()

    async def process(self, payload: dict) -> list[dict]:
        return await super().process(payload, self.parse)
