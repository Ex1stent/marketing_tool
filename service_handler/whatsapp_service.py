from __future__ import annotations

from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from utils import graph
from utils.decorators import _tool

load_dotenv()


def register_whatsapp_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    async def whatsapp_message(number: str, message: str) -> dict[str, Any]:
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages",
            messaging_product="whatsapp",
            to=number,
            type="text",
            text={"body": message},
        )

    @tool
    async def whatsapp_imagemessage(number: str, image_url: str) -> dict[str, Any]:
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages",
            messaging_product="whatsapp",
            to=number,
            type="image",
            image={"link": image_url},
        )

    @tool
    async def whatsapp_videomessage(number: str, video_url: str) -> dict[str, Any]:
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages",
            messaging_product="whatsapp",
            to=number,
            type="video",
            video={"link": video_url},
        )

    @tool
    async def whatsapp_documentmessage(number: str, document_url: str) -> dict[str, Any]:
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages",
            messaging_product="whatsapp",
            to=number,
            type="document",
            document={"link": document_url},
        )

    @tool
    async def whatsapp_templatemessage(
        number: str,
        template_name: str,
        language: str,
        components: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return await graph.whatsapp_post(
            f"{graph.whatsapp_id()}/messages",
            messaging_product="whatsapp",
            to=number,
            type="template",
            template={
                "name": template_name,
                "language": language,
                "components": components,
            },
        )
