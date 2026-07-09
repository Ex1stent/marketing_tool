import json
import os
import re

from anthropic import Anthropic
from pypdf import PdfReader
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelProvider:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
        )
        self.model = os.getenv("ANTHROPIC_MODEL")
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> str:
        path = os.getenv("DOCUMENT_PATH")
        if not path:
            return ""
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    def _parse_json_response(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.S)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        match = re.search(r"\{.*\}", content, flags=re.S)
        if match:
            return json.loads(match.group(0))

        raise json.JSONDecodeError("Could not parse JSON response", content, 0)

    def classify_and_reply(self, platform: str, event_type: str, text: str) -> dict:
        logger.info("Classifying and replying to event: %s", event_type)
        system_prompt = f"""


You are the Support Assistant for nyalazone.ai.

Knowledge Base:
{self.knowledge_base}


Rules:
- Reply only to questions related to nyalazone.ai, its services, features, pricing, onboarding, usage, support, or business context.
- If the user asks anything unrelated to nyalazone.ai, do not answer the unrelated question.
- For unrelated questions, return JSON with should_reply=false.
- Keep replies short, helpful, and business-safe.
- Never answer general knowledge, coding, politics, entertainment, health, finance, or personal questions unless they are directly about nyalazone.ai.
- The knowledge base above is the authoritative source.
- Always answer from it.
- If the answer is not present in the knowledge base, respond that the information is unavailable.
- Do not invent features or policies.
- Return ONLY valid JSON.
- Do not wrap the JSON in markdown or code fences.
- reply_text should be under 1000 characters

Output format:
{{
  "should_reply": true,
  "reply_text": "short helpful reply",
  "reason": "why"
}}
"""

        user_prompt = f"""
Platform: {platform}
Event type: {event_type}
User text: {text}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

        content = response.content[0].text.strip()
        return self._parse_json_response(content)


