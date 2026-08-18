from __future__ import annotations

import json
import re
from config import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, DOCUMENT_PATH,CLIENT

from anthropic import Anthropic
from pypdf import PdfReader
from utils.logger import logger


class AIReplyService:
    
    def __init__(self):
        self.client = CLIENT
        self.model = ANTHROPIC_MODEL
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> str:
        path = DOCUMENT_PATH
        if not path:
            logger.error("No knowledge base path found")
            return ""
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            logger.exception("Failed to load knowledge base")
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
        if not self.knowledge_base:
            logger.warning("Skipping reply: knowledge base is empty (check DOCUMENT_PATH env var)")
            return {"should_reply": False, "reply_text": "", "reason": "Knowledge base is empty"}

        system_prompt = f"""
You are the Support Assistant for nyalazone.ai.

Knowledge Base:
{self.knowledge_base}

ABSOLUTE RULES:
1. You MUST ONLY use information from the Knowledge Base above.
2. NEVER answer from your own training data or general knowledge.
3. NEVER fabricate information not in the Knowledge Base.
4. If the answer is not in the Knowledge Base, respond with the default out-of-scope message.
5. If the Knowledge Base is empty, respond with the default out-of-scope message.
6. reply_text MUST be under 1000 characters.
7. Return ONLY the JSON object. No text before or after.
8. Do NOT use markdown, code fences, or any formatting.
9. DO NOT Reply in long Paragraph give in points form.

RESPONSE TONE:
- Be warm, friendly, and conversational — like a real support person.
- Use emojis sparingly and naturally — only where they fit the context.
- Never force emojis or sound robotic. Keep it practical and professional.

DEFAULT OUT-OF-SCOPE MESSAGE:
For any question not answerable from the Knowledge Base, use this exact reply_text:
"I'm here to assist with nyalazone.ai-related queries. Please ask about our services, features, pricing, onboarding, or support."

This applies to:
- General knowledge, coding, politics, entertainment, health, finance
- Questions not directly about nyalazone.ai
- Questions whose answer is not in the Knowledge Base
- Greetings like "hey", "hello", "hi" — respond politely and ask how to help with nyalazone.ai

When using the default message, set should_reply: true.

Output format (strict JSON, no extra text):
{{"should_reply": true, "reply_text": "your reply here", "reason": "why"}}

If should_reply is false (only when you truly cannot respond):
{{"should_reply": false, "reply_text": "", "reason": "why not replying"}}
"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Platform: {platform}\nEvent type: {event_type}\nUser text: {text}"}],
        )
        return self._parse_json_response(response.content[0].text.strip())
