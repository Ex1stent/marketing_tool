from __future__ import annotations

from typing import Any

from config import MCP_SERVER_URL
from mcp import ClientSession
from mcp.client.sse import sse_client


class ChatCore:
    
    def __init__(self, system_prompt: str, mcp_server_url: str = MCP_SERVER_URL):
        self.system_prompt = system_prompt
        self.mcp_server_url = mcp_server_url

    def _serialize_content(self, content: Any) -> Any:
        if hasattr(content, "text"):
            return content.text
        if hasattr(content, "model_dump"):
            return content.model_dump(mode="json")
        return str(content)

    def _format_tool_result(self, result: Any) -> dict[str, Any]:              # format Claude expects.
        return {
            "isError": result.isError,
            "content": [self._serialize_content(item) for item in result.content],
        }

    def _convert_tools_for_api(self, tools: list[Any]) -> list[dict[str, Any]]:     #Convert MCP tool definitions into Anthropic's tool format.
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in tools
        ]

    def _blocks_to_message(self, blocks: list[Any]) -> list[dict[str, Any]]:     # Convert Claude's message blocks into plain dictionary
        message_blocks: list[dict[str, Any]] = []
        for block in blocks:
            if block.type == "text":
                message_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                message_blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        return message_blocks

    def _extract_response_text(self, blocks: list[Any]) -> str:
        return "\n".join(block.text for block in blocks if block.type == "text").strip()

    async def _get_tools(self, session):
        tools_result = await session.list_tools()
        return self._convert_tools_for_api(tools_result.tools)

    async def _call_claude(self, client, model, conversation, tools):
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0.2,
            system=self.system_prompt,
            messages=conversation,
            tools=tools,
        )
        assistant_blocks = self._blocks_to_message(response.content)
        conversation.append({"role": "assistant", "content": assistant_blocks})
        return response

    async def _execute_tools(self, session, tool_uses):     # Execute the MCP tools and return the results
        tool_results = []
        for t in tool_uses:
            result = await session.call_tool(t.name, t.input)
            payload = self._format_tool_result(result)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": t.id,
                "is_error": payload["isError"],
                "content": payload["content"][0] if payload["content"] else "",
            })
        return tool_results

    async def _chat_loop(self, client, model, conversation, tools, session):
        while True:
            response = await self._call_claude(client, model, conversation, tools)
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                return self._extract_response_text(response.content)
            tool_results = await self._execute_tools(session, tool_uses)
            conversation.append({"role": "user", "content": tool_results})

    async def chat_once(self, conversation, client, model):
        async with sse_client(self.mcp_server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await self._get_tools(session)
                return await self._chat_loop(client, model, conversation, tools, session)
