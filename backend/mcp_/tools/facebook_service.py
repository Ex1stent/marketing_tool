from __future__ import annotations

from typing import Any
from config import FACEBOOK_PAGE_ID

from mcp.server.fastmcp import FastMCP
from utils import graph
from utils.decorators import _tool


async def create_page_post(message: str, image_url: str | None = None) -> dict[str, Any]:
    if image_url:
        return await graph.facebook_post(f"{FACEBOOK_PAGE_ID}/photos", url=image_url.strip(), caption=message)
    return await graph.facebook_post(f"{FACEBOOK_PAGE_ID}/feed", message=message)


async def send_page_message(recipient_id: str, text: str) -> dict[str, Any]:
    return await graph.facebook_post(
        f"{FACEBOOK_PAGE_ID}/messages",
        recipient={"id": recipient_id},
        message={"text": text},
        messaging_type="RESPONSE",
    )


def register_facebook_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)


    @tool
    async def get_page_profile(fields: str | None = None) -> dict[str, Any]:
        """Get the Facebook Page profile.

        Args:
            fields: Optional comma-separated list of fields to return;
                defaults to id, name, about, category, category_list,
                fan_count, followers_count, phone, website, emails.

        Returns:
            dict with the requested profile fields.
        """
        return await graph.facebook_get(
            FACEBOOK_PAGE_ID,
            fields=fields or "id,name,about,category,category_list,fan_count,followers_count,phone,website,emails",
        )

    @tool
    async def create_page_post_tool(message: str, image_url: str | None = None) -> dict[str, Any]:
        """Create a new post on the Facebook Page.

        Args:
            message: Text content of the post.
            image_url: Optional public HTTPS URL of an image to attach.

        Returns:
            dict with the created post or photo response.
        """
        return await create_page_post(message=message, image_url=image_url)

    @tool
    async def list_page_posts(limit: int = 25, after: str | None = None) -> dict[str, Any]:
        """List recent posts from the Facebook Page feed.

        Args:
            limit: Maximum number of posts to return (default 25).
            after: Optional pagination cursor from a previous response.

        Returns:
            dict with the page's posts and pagination info.
        """
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/feed",
            fields="id,message,created_time,permalink_url,likes.limit(1).summary(true),comments.limit(1).summary(true)",
            limit=limit,
            after=after,
        )

    @tool
    async def get_page_post(post_id: str) -> dict[str, Any]:
        """Get a single Facebook Page post by ID.

        Args:
            post_id: ID of the post to fetch.

        Returns:
            dict with the post and its engagement summary.
        """
        return await graph.facebook_get(
            post_id,
            fields="id,message,created_time,permalink_url,likes.limit(1).summary(true),comments.limit(1).summary(true)",
        )

    @tool
    async def delete_page_post(post_id: str) -> dict[str, Any]:
        """Delete a Facebook Page post by ID.

        Args:
            post_id: ID of the post to delete.

        Returns:
            dict with the deletion result.
        """
        return await graph.facebook_delete(post_id)

    @tool
    async def list_page_comments(post_id: str, limit: int = 25) -> dict[str, Any]:
        """List comments on a Facebook post.

        Args:
            post_id: ID of the post whose comments to list.
            limit: Maximum number of comments to return (default 25).

        Returns:
            dict with the comments list.
        """
        return await graph.facebook_get(
            f"{post_id}/comments",
            fields="id,message,from,created_time,like_count,comment_count",
            limit=limit,
        )

    @tool
    async def reply_to_page_comment(comment_id: str, message: str) -> dict[str, Any]:
        """Post a reply to a Facebook comment.

        Args:
            comment_id: ID of the comment to reply to.
            message: Text of the reply.

        Returns:
            dict with the reply result.
        """
        return await graph.facebook_post(f"{comment_id}/comments", message=message)

    @tool
    async def send_page_message_tool(recipient_id: str, text: str) -> dict[str, Any]:
        """Send a private message to a user from the Facebook Page.

        Args:
            recipient_id: PSID of the recipient user.
            text: Text of the message.

        Returns:
            dict with the message send result.
        """
        return await send_page_message(recipient_id=recipient_id, text=text)

    @tool
    async def get_page_conversations(limit: int = 20) -> dict[str, Any]:
        """List the Page's recent conversations.

        Args:
            limit: Maximum number of conversations to return (default 20).

        Returns:
            dict with the conversations list.
        """
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/conversations",
            fields="id,updated_time,message_count,participants",
            limit=limit,
        )

    @tool
    async def get_page_conversation(conversation_id: str) -> dict[str, Any]:
        """Get a single conversation and its recent messages.

        Args:
            conversation_id: ID of the conversation to fetch.

        Returns:
            dict with the conversation and up to 50 messages.
        """
        return await graph.facebook_get(
            conversation_id,
            fields="messages.limit(50){id,from,to,message,created_time},participants,updated_time",
        )

    @tool
    async def get_page_insights(
        metrics: str = "page_post_engagements,page_total_media_view_unique,page_follows",
        period: str = "day",
        since: int | None = None,
        until: int | None = None,
    ) -> dict[str, Any]:
        """Get Page insights metrics over a time range.

        Args:
            metrics: Comma-separated metric names (default
                page_follows,page_post_engagements,page_impressions_unique).
            period: Aggregation period: day, week, or days_28 (default day).
            since: Optional start timestamp as Unix seconds.
            until: Optional end timestamp as Unix seconds.

        Returns:
            dict with the requested insights values.
        """
        return await graph.facebook_get(
            f"{FACEBOOK_PAGE_ID}/insights",
            metric=metrics,
            period=period,
            since=since,
            until=until,
        )
