from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from config import FACEBOOK_PAGE_ID
from utils import graph
from utils.decorators import _tool


def register_facebook_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    async def get_page_profile(fields: str | None = None) -> dict[str, Any]:
        """Get Facebook Page profile info."""
        return await graph.facebook_get(
            FACEBOOK_PAGE_ID,
            fields=fields or "id,name,about,category,category_list,fan_count,followers_count,phone,website,emails",
        )

    @tool
    async def create_page_post(message: str, link: str | None = None) -> dict[str, Any]:
        """Create a new post on the Facebook Page feed."""
        return await graph.facebook_post(f"{FACEBOOK_PAGE_ID}/feed", message=message, link=link)

    @tool
    async def list_page_posts(limit: int = 25, after: str | None = None) -> dict[str, Any]:
        """List recent posts from the Page feed."""
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/feed",
            fields="id,message,created_time,permalink_url,type,likes.limit(1).summary(true),comments.limit(1).summary(true)",
            limit=limit,
            after=after,
        )

    @tool
    async def get_page_post(post_id: str) -> dict[str, Any]:
        """Get a single Facebook Page post by ID."""
        return await graph.facebook_get(
            post_id,
            fields="id,message,created_time,permalink_url,type,likes.summary(true),comments.summary(true),shares",
        )

    @tool
    async def delete_page_post(post_id: str) -> dict[str, Any]:
        """Delete a Facebook Page post."""
        return await graph.facebook_delete(post_id)

    @tool
    async def list_page_comments(post_id: str, limit: int = 25) -> dict[str, Any]:
        """List comments on a Facebook Page post."""
        return await graph.facebook_get(
            f"{post_id}/comments",
            fields="id,message,from,created_time,like_count,comment_count",
            limit=limit,
        )

    @tool
    async def reply_to_page_comment(comment_id: str, message: str) -> dict[str, Any]:
        """Reply to a comment on a Facebook Page post."""
        return await graph.facebook_post(f"{comment_id}/comments", message=message)

    @tool
    async def send_page_message(recipient_id: str, text: str) -> dict[str, Any]:
        """Send a Messenger message from the Page to a user."""
        return await graph.facebook_post(
            f"{FACEBOOK_PAGE_ID}/messages",
            recipient={"id": recipient_id},
            message={"text": text},
            messaging_type="RESPONSE",
        )

    @tool
    async def get_page_conversations(limit: int = 20) -> dict[str, Any]:
        """List Messenger conversations for the Page."""
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/conversations",
            fields="id,updated_time,message_count,participants",
            limit=limit,
        )

    @tool
    async def get_page_conversation(conversation_id: str) -> dict[str, Any]:
        """Get messages in a Messenger conversation."""
        return await graph.facebook_get(
            conversation_id,
            fields="messages.limit(50){id,from,to,message,created_time},participants,updated_time",
        )

    @tool
    async def get_page_insights(
        metrics: str = "page_impressions,page_engaged_users,page_fan_count",
        period: str = "day",
        since: int | None = None,
        until: int | None = None,
    ) -> dict[str, Any]:
        """Get Page-level analytics."""
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/insights",
            metric=metrics,
            period=period,
            since=since,
            until=until,
        )
