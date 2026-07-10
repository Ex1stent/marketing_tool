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
            logger.error("No knowledge base path found")
            return ""
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            logger.error("Failed to load knowledge base")
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
            logger.error("Knowledge base is empty")
            return {"should_reply": False, "reply_text": "", "reason": "Knowledge base is empty"}
        if not self.client or not self.model:
            logger.error("Model not initialized")
            return {"should_reply": False, "reply_text": "", "reason": "Model not initialized"}
        
        
        logger.info("Classifying and replying to event: %s", event_type)
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

#         system_prompt = f"""


# You are the Support Assistant for nyalazone.ai.

# Knowledge Base:
# {self.knowledge_base}


# Rules:
# - Reply only to questions related to nyalazone.ai, its services, features, pricing, onboarding, usage, support, or business context.
# - If the user asks anything unrelated to nyalazone.ai, do not answer the unrelated question.
# - For unrelated questions, return JSON with should_reply=false.
# - Keep replies short, helpful, and business-safe.
# - Never answer general knowledge, coding, politics, entertainment, health, finance, or personal questions unless they are directly about nyalazone.ai.
# - The knowledge base above is the authoritative source.
# - Always answer from it.
# - If the answer is not present in the knowledge base, respond that the information is unavailable.
# - Do not invent features or policies.
# - Return ONLY valid JSON.
# - Do not wrap the JSON in markdown or code fences.
# - reply_text should be under 1000 characters

# Output format:
# {{
#   "should_reply": true,
#   "reply_text": "short helpful reply",
#   "reason": "why"
# }}
# """

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


