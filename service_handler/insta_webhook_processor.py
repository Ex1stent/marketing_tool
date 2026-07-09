from __future__ import annotations

from core.insta_parse import InstaWebhookParser
from core.base_webhook_processor import BaseWebhookProcessor


class InstaWebhookProcessor(BaseWebhookProcessor):
    def __init__(self):
        super().__init__()
        self.parse = InstaWebhookParser()

    async def process(self, payload: dict):
        return await super().process(payload, self.parse)
