from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from utils import graph
from utils.decorators import _tool


async def send_whatsapp_message(number: str, message: str) -> dict[str, Any]:
    return await graph.whatsapp_post(
        f"{graph.whatsapp_id()}/messages",
        messaging_product="whatsapp",
        to=number,
        type="text",
        text={"body": message},
    )


async def send_whatsapp_image(number: str, image_url: str, caption: str | None = None) -> dict[str, Any]:
    image = {"link": image_url}
    if caption:
        image["caption"] = caption
    return await graph.whatsapp_post(
        f"{graph.whatsapp_id()}/messages",
        messaging_product="whatsapp",
        to=number,
        type="image",
        image=image,
    )


async def send_whatsapp_video(number: str, video_url: str, caption: str | None = None) -> dict[str, Any]:
    video = {"link": video_url}
    if caption:
        video["caption"] = caption
    return await graph.whatsapp_post(
        f"{graph.whatsapp_id()}/messages",
        messaging_product="whatsapp",
        to=number,
        type="video",
        video=video,
    )


def register_whatsapp_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    async def whatsapp_message(number: str, message: str) -> dict[str, Any]:
        """Send a plain text message over WhatsApp to a phone number.

        Args:
            number: Recipient phone number in E.164 format (e.g. 919876543210).
            message: Text body of the message.

        Returns:
            dict with the WhatsApp API response.
        """
        return await send_whatsapp_message(number=number, message=message)

    @tool
    async def whatsapp_imagemessage(number: str, image_url: str) -> dict[str, Any]:
        """Send an image over WhatsApp to a phone number.

        Args:
            number: Recipient phone number in E.164 format (e.g. 919876543210).
            image_url: Public HTTPS URL of the image to send.

        Returns:
            dict with the WhatsApp API response.
        """
        return await send_whatsapp_image(number=number, image_url=image_url)

    @tool
    async def whatsapp_videomessage(number: str, video_url: str) -> dict[str, Any]:
        """Send a video over WhatsApp to a phone number.

        Args:
            number: Recipient phone number in E.164 format (e.g. 919876543210).
            video_url: Public HTTPS URL of the video to send.

        Returns:
            dict with the WhatsApp API response.
        """
        return await send_whatsapp_video(number=number, video_url=video_url)

    @tool
    async def whatsapp_documentmessage(number: str, document_url: str) -> dict[str, Any]:
        """Send a document over WhatsApp to a phone number.

        Args:
            number: Recipient phone number in E.164 format (e.g. 919876543210).
            document_url: Public HTTPS URL of the document to send.

        Returns:
            dict with the WhatsApp API response.
        """
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
        """Send a pre-approved template message over WhatsApp.

        Args:
            number: Recipient phone number in E.164 format (e.g. 919876543210).
            template_name: Name of the approved template to send.
            language: Language code of the template (e.g. "en_US").
            components: list of template component dicts for variables and media.

        Returns:
            dict with the WhatsApp API response.
        """
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
