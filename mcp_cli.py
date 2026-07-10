import argparse
import json
import os
from typing import Any

import anyio
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from service_handler.providers import ModelProvider


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp/sse")

load_dotenv("./.env")

model_provider = ModelProvider()



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

OUT OF SCOPE (do not answer):
- General knowledge, coding, politics, entertainment, health, finance
- Questions not directly about nyalazone.ai
- Questions whose answer is not in the Knowledge Base

For out-of-scope questions, reply: "I can only assist with nyalazone.ai-related questions."
"""


def _content_to_jsonable(content: Any) -> Any:
    if hasattr(content, "text"):
        return content.text
    if hasattr(content, "model_dump"):
        return content.model_dump(mode="json")
    return str(content)


def _tool_result_payload(result: Any) -> dict[str, Any]:
    return {
        "isError": result.isError,
        "structuredContent": result.structuredContent,
        "content": [_content_to_jsonable(item) for item in result.content],
    }


def _anthropic_tools(tools: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        }
        for tool in tools
    ]


def _assistant_blocks_to_message(blocks: list[Any]) -> list[dict[str, Any]]:
    message_blocks: list[dict[str, Any]] = []
    for block in blocks:
        if block.type == "text":
            message_blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            message_blocks.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
    return message_blocks


def _render_assistant_text(blocks: list[Any]) -> str:
    return "\n".join(block.text for block in blocks if block.type == "text").strip()


async def _run_list_tools() -> None:
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()
            payload = {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in result.tools
                ]
            }
            print(json.dumps(payload, indent=2))


async def _run_call_tool(tool_name: str, tool_args: dict[str, Any]) -> None:
    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            print(json.dumps(_tool_result_payload(result), indent=2))


async def _chat_once(
    session: ClientSession,
    client: Anthropic,
    model: str,
    system_prompt: str,
    conversation: list[dict[str, Any]],
) -> str:
    tools_result = await session.list_tools()
    anthropic_tools = _anthropic_tools(tools_result.tools)

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0.2,
            system=system_prompt,
            messages=conversation,
            tools=anthropic_tools,
        )

        assistant_blocks = _assistant_blocks_to_message(response.content)
        conversation.append({"role": "assistant", "content": assistant_blocks})

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            return _render_assistant_text(response.content)

        tool_results = []
        for tool_use in tool_uses:
            result = await session.call_tool(tool_use.name, tool_use.input)
            tool_payload = _tool_result_payload(result)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "is_error": tool_payload["isError"],
                    "content": json.dumps(tool_payload, ensure_ascii=True),
                }
            )

        conversation.append({"role": "user", "content": tool_results})


async def _run_chat(prompt: str | None, system_prompt: str) -> None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    if not model_provider.knowledge_base or not model_provider.knowledge_base.strip():
        raise SystemExit("Knowledge base is empty. Set DOCUMENT_PATH in .env to a valid PDF file.")

    model = os.getenv("ANTHROPIC_MODEL")
    client = Anthropic(api_key=api_key)

    async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            conversation: list[dict[str, Any]] = []

            if prompt is not None:
                conversation.append({"role": "user", "content": prompt})
                answer = await _chat_once(session, client, model, system_prompt, conversation)
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
                answer = await _chat_once(session, client, model, system_prompt, conversation)
                if answer:
                    print(f"Claude: {answer}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI helper for the local MCP server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools", help="List tools exposed by the MCP server")

    call_parser = subparsers.add_parser("call-tool", help="Call a tool with JSON args")
    call_parser.add_argument("tool_name", help="Tool name to call")
    call_parser.add_argument(
        "--args",
        default="{}",
        help='JSON object of tool arguments, for example: --args "{\\"limit\\": 5}"',
    )

    chat_parser = subparsers.add_parser("chat", help="Chat with Anthropic using MCP tools")
    chat_parser.add_argument(
        "--prompt",
        help="Single prompt to run once. If omitted, starts an interactive chat loop.",
    )
    chat_parser.add_argument(
        "--system",
        default=DEFAULT_SYSTEM_PROMPT,
        help="Optional system prompt override for the Anthropic chat loop.",
    )

    args = parser.parse_args()

    if args.command == "list-tools":
        anyio.run(_run_list_tools)
        return

    if args.command == "call-tool":
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON passed to --args: {exc}") from exc

        if not isinstance(tool_args, dict):
            raise SystemExit("--args must decode to a JSON object")

        anyio.run(_run_call_tool, args.tool_name, tool_args)
        return

    if args.command == "chat":
        anyio.run(_run_chat, args.prompt, args.system)


if __name__ == "__main__":
    main()
