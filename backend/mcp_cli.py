import argparse
import json
from typing import Any
from config import ANTHROPIC_MODEL, MCP_SERVER_URL, CLIENT
from services.chat_core import ChatCore

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

from services.ai_reply_service import AIReplyService

model_provider = AIReplyService()

DEFAULT_SYSTEM_PROMPT = f"""
You are the Support Assistant for nyalazone.ai.

Knowledge Base:
{model_provider.knowledge_base}

ABSOLUTE RULES:
1. You MUST ONLY use information from the Knowledge Base above.
2. NEVER answer from your own training data or general knowledge.
3. NEVER fabricate information not in the Knowledge Base.
4. If the answer is not in the Knowledge Base, say so clearly.
5. If the Knowledge Base is empty, tell the user the knowledge base is unavailable.
6. Keep replies short, helpful, and business-safe.
7. Do NOT use markdown formatting.
8. Always generate data in excel with topic(if matching with knowledge base only). If there is no topic provided generate with defualt topic in knowledge base.
9. Always verify and ask before saving data in excel.
10. For scheduling posts from Excel:
    - First call preview_excel_posts to show the user what will be scheduled.
    - Present the preview in a clear table format.
    - Ask the user to confirm before saving.
    - Only confirm schedule_posts AFTER the user explicitly confirms.
11. Do NOT schedule posts with a scheduled_time that has already passed.
    When previewing posts, clearly inform the user if any posts were skipped
    because their scheduled time is in the past.
12. DO NOT Reply about Support Considerations.
13. DO NOT Reply about Negatives,Concerns,Complaints,Issues,Feedback,Suggestions,Criticism or any other Negative topic.

OUT OF SCOPE (do not answer):
- General knowledge, coding, politics, entertainment, health, finance
- Questions not directly about nyalazone.ai
- Questions whose answer is not in the Knowledge Base

For out-of-scope questions, reply: "I can only assist with nyalazone.ai-related questions."

AVAILABLE TOOLS:
- Instagram: publish_image_tool, publish_reel_tool, publish_story_tool, publish_carousel_tool
- Facebook: create_page_post_tool
- WhatsApp: whatsapp_message, whatsapp_imagemessage, whatsapp_documentmessage, whatsapp_videomessage
- Excel: schedule_posts_from_excel, read_excel_cell, update_excel_cell
- Scheduling: list_scheduled_posts, cancel_scheduled_post, update_scheduled_post

When posting images to Instagram or Facebook, use the File URL provided with each image message.
The URL is a public link that Instagram/Facebook can fetch directly.
For Excel files, use schedule_posts_from_excel.
"""

_chat = ChatCore(system_prompt=DEFAULT_SYSTEM_PROMPT)


async def _run_list_tools() -> None:
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            payload = {
                "tools": [
                    {"name": tool.name, "description": tool.description, "inputSchema": tool.inputSchema}
                    for tool in result.tools
                ]
            }
            print(json.dumps(payload, indent=2))


async def _run_call_tool(tool_name: str, tool_args: dict[str, Any]) -> None:
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            print(json.dumps(_chat._format_tool_result(result), indent=2))


async def _run_chat(prompt: str | None, system_prompt: str) -> None:
    chat = ChatCore(system_prompt=system_prompt)
    conversation: list[dict[str, Any]] = []

    if prompt is not None:
        conversation.append({"role": "user", "content": prompt})
        answer = await chat.chat_once(conversation, CLIENT, ANTHROPIC_MODEL)
        print(answer)
        return

    print("Anthropic MCP chat. Type 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        conversation.append({"role": "user", "content": user_input})
        answer = await chat.chat_once(conversation, CLIENT, ANTHROPIC_MODEL)
        if answer:
            print(f"Claude: {answer}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI helper for the local MCP server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools", help="List tools exposed by the MCP server")

    call_parser = subparsers.add_parser("call-tool", help="Call a tool with JSON args")
    call_parser.add_argument("tool_name", help="Tool name to call")
    call_parser.add_argument("--args", default="{}", help='JSON object of tool arguments, for example: --args "{\\"limit\\": 5}"')

    chat_parser = subparsers.add_parser("chat", help="Chat with Anthropic using MCP tools")
    chat_parser.add_argument("--prompt", help="Single prompt to run once. If omitted, starts an interactive chat loop.")
    chat_parser.add_argument("--system", default=DEFAULT_SYSTEM_PROMPT, help="Optional system prompt override for the Anthropic chat loop.")

    args = parser.parse_args()

    if args.command == "list-tools":
        asyncio.run(_run_list_tools())
        return

    if args.command == "call-tool":
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON passed to --args: {exc}") from exc

        if not isinstance(tool_args, dict):
            raise SystemExit("--args must decode to a JSON object")

        asyncio.run(_run_call_tool(args.tool_name, tool_args))
        return

    if args.command == "chat":
        asyncio.run(_run_chat(args.prompt, args.system))


if __name__ == "__main__":
    main()
