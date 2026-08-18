from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from utils import graph
from utils.decorators import _tool

DEFAULT_PROFILE_FIELDS = (
    "id,username,name,biography,followers_count,follows_count,"
    "media_count,profile_picture_url,website"
)
DEFAULT_MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
    "permalink,timestamp,like_count,comments_count"
)
DEFAULT_HASHTAG_MEDIA_FIELDS = (
    "id,caption,media_type,permalink,timestamp,like_count,comments_count"
)


async def _wait_container(container_id: str, timeout_s: int = 300) -> None:
    elapsed = 0
    while elapsed < timeout_s:
        res = await graph.get(container_id, fields="status_code,status")
        code = res.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise graph.GraphError(
                0,
                {"error": {"message": f"container {container_id} status={code}", "code": -1}},
            )
        await asyncio.sleep(3)
        elapsed += 3
    raise TimeoutError(f"container {container_id} did not finish within {timeout_s}s")


async def _publish(container_id: str) -> dict[str, Any]:
    return await graph.post(f"{graph.ig_account_id()}/media_publish", creation_id=container_id)


async def publish_image(
    image_url: str,
    caption: str | None = None,
    location_id: str | None = None,
) -> dict[str, Any]:
    container = await graph.post(
        f"{graph.ig_account_id()}/media",
        image_url=image_url,
        caption=caption,
        location_id=location_id,
    )
    return await _publish(container["id"])


async def publish_reel(
    video_url: str,
    caption: str | None = None,
    share_to_feed: bool = True,
    cover_url: str | None = None,
    thumb_offset: int | None = None,
) -> dict[str, Any]:
    container = await graph.post(
        f"{graph.ig_account_id()}/media",
        media_type="REELS",
        video_url=video_url,
        caption=caption,
        share_to_feed=str(share_to_feed).lower(),
        cover_url=cover_url,
        thumb_offset=thumb_offset,
    )
    await _wait_container(container["id"])
    return await _publish(container["id"])


async def publish_story(
    image_url: str | None = None,
    video_url: str | None = None,
) -> dict[str, Any]:
    if bool(image_url) == bool(video_url):
        raise ValueError("Provide exactly one of image_url or video_url")
    container = await graph.post(
        f"{graph.ig_account_id()}/media",
        media_type="STORIES",
        image_url=image_url,
        video_url=video_url,
    )
    if video_url:
        await _wait_container(container["id"])
    return await _publish(container["id"])


async def publish_carousel(
    items: list[dict[str, str]],
    caption: str | None = None,
) -> dict[str, Any]:
    if not 2 <= len(items) <= 10:
        raise ValueError("Carousel must contain between 2 and 10 items")

    child_ids: list[str] = []
    for item in items:
        if "image_url" in item:
            child = await graph.post(
                f"{graph.ig_account_id()}/media",
                is_carousel_item="true",
                image_url=item["image_url"],
            )
        elif "video_url" in item:
            child = await graph.post(
                f"{graph.ig_account_id()}/media",
                is_carousel_item="true",
                media_type="VIDEO",
                video_url=item["video_url"],
            )
            await _wait_container(child["id"])
        else:
            raise ValueError(f"Carousel item must contain image_url or video_url: {item}")
        child_ids.append(child["id"])

    parent = await graph.post(
        f"{graph.ig_account_id()}/media",
        media_type="CAROUSEL",
        children=",".join(child_ids),
        caption=caption,
    )
    return await _publish(parent["id"])


def register_instagram_tools(mcp: FastMCP) -> None:
    tool = _tool(mcp)

    @tool
    async def get_my_profile(fields: str | None = None) -> dict[str, Any]:
        """Get the connected Instagram professional account's profile.

        Args:
            fields: Optional comma-separated list of fields to return;
                defaults to id, username, name, biography, followers_count,
                follows_count, media_count, profile_picture_url, website.

        Returns:
            dict with the requested profile fields.
        """
        return await graph.get(graph.ig_account_id(), fields=fields or DEFAULT_PROFILE_FIELDS)

    @tool
    async def list_my_media(
        limit: int = 25,
        after: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """List the account's recent media, paginated.

        Args:
            limit: Maximum number of media to return (default 25).
            after: Optional pagination cursor from a previous response.
            fields: Optional comma-separated list of fields to return;
                defaults to id, caption, media_type, media_product_type,
                media_url, thumbnail_url, permalink, timestamp, like_count,
                comments_count.

        Returns:
            dict with the media list and pagination info.
        """
        return await graph.get(
            f"{graph.ig_account_id()}/media",
            fields=fields or DEFAULT_MEDIA_FIELDS,
            limit=limit,
            after=after,
        )

    @tool
    async def list_all_media(
        max_pages: int = 5,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Fetch all the account's media across multiple pages.

        Args:
            max_pages: Maximum number of pages to follow (default 5).
            fields: Optional comma-separated list of fields to return; same
                defaults as list_my_media.

        Returns:
            dict with the aggregated media list.
        """
        return await graph.paginate(
            f"{graph.ig_account_id()}/media",
            max_pages=max_pages,
            fields=fields or DEFAULT_MEDIA_FIELDS,
        )

    @tool
    async def get_media(media_id: str, fields: str | None = None) -> dict[str, Any]:
        """Get a single Instagram media object by ID.

        Args:
            media_id: ID of the media to fetch.
            fields: Optional comma-separated list of fields to return; same
                defaults as list_my_media.

        Returns:
            dict with the media fields.
        """
        return await graph.get(media_id, fields=fields or DEFAULT_MEDIA_FIELDS)

    @tool
    async def list_tagged_media(limit: int = 25, fields: str | None = None) -> dict[str, Any]:
        """List media where the connected account is tagged.

        Args:
            limit: Maximum number of media to return (default 25).
            fields: Optional comma-separated list of fields to return; same
                defaults as list_my_media.

        Returns:
            dict with the tagged media list.
        """
        return await graph.get(
            f"{graph.ig_account_id()}/tags",
            fields=fields or DEFAULT_MEDIA_FIELDS,
            limit=limit,
        )

    @tool
    async def list_stories() -> dict[str, Any]:
        """List the account's active stories.

        Returns:
            dict with the stories list.
        """
        return await graph.get(
            f"{graph.ig_account_id()}/stories",
            fields="id,media_type,media_url,permalink,timestamp",
        )

    @tool
    async def search_hashtag(query: str) -> dict[str, Any]:
        """Search for an Instagram hashtag by name.

        Args:
            query: Hashtag to search for; the leading # is optional.

        Returns:
            dict with the matching hashtag and its ID.
        """
        return await graph.get("ig_hashtag_search", user_id=graph.ig_user_id(), q=query.lstrip("#"))

    @tool
    async def hashtag_top_media(hashtag_id: str, fields: str | None = None) -> dict[str, Any]:
        """Get top media for a hashtag.

        Args:
            hashtag_id: ID of the hashtag.
            fields: Optional comma-separated list of fields to return;
                defaults to id, caption, media_type, permalink, timestamp,
                like_count, comments_count.

        Returns:
            dict with the top media list.
        """
        return await graph.get(
            f"{hashtag_id}/top_media",
            user_id=graph.ig_user_id(),
            fields=fields or DEFAULT_HASHTAG_MEDIA_FIELDS,
        )

    @tool
    async def hashtag_recent_media(hashtag_id: str, fields: str | None = None) -> dict[str, Any]:
        """Get the most recent media for a hashtag.

        Args:
            hashtag_id: ID of the hashtag.
            fields: Optional comma-separated list of fields to return; same
                defaults as hashtag_top_media.

        Returns:
            dict with the recent media list.
        """
        return await graph.get(
            f"{hashtag_id}/recent_media",
            user_id=graph.ig_user_id(),
            fields=fields or DEFAULT_HASHTAG_MEDIA_FIELDS,
        )

    @tool
    async def publish_image_tool(
        image_url: str,
        caption: str | None = None,
        location_id: str | None = None,
    ) -> dict[str, Any]:
        """Publish a single image to the Instagram feed.

        Args:
            image_url: Public HTTPS URL of the image to publish.
            caption: Optional caption for the post.
            location_id: Optional Instagram location ID to tag the post with.

        Returns:
            dict with the publish result.
        """
        return await publish_image(image_url=image_url, caption=caption, location_id=location_id)

    @tool
    async def publish_reel_tool(
        video_url: str,
        caption: str | None = None,
        share_to_feed: bool = True,
        cover_url: str | None = None,
        thumb_offset: int | None = None,
    ) -> dict[str, Any]:
        """Publish a video as an Instagram Reel.

        Args:
            video_url: Public HTTPS URL of the video to publish.
            caption: Optional caption for the reel.
            share_to_feed: Whether to also share the reel to the main feed
                (default true).
            cover_url: Optional public HTTPS URL of the cover image.
            thumb_offset: Optional thumbnail offset in milliseconds.

        Returns:
            dict with the publish result.
        """
        return await publish_reel(video_url=video_url, caption=caption, share_to_feed=share_to_feed, cover_url=cover_url, thumb_offset=thumb_offset)

    @tool
    async def publish_story_tool(
        image_url: str | None = None,
        video_url: str | None = None,
    ) -> dict[str, Any]:
        """Publish an image or video as an Instagram Story.

        Provide exactly one of image_url or video_url.

        Args:
            image_url: Public HTTPS URL of the image to publish (mutually
                exclusive with video_url).
            video_url: Public HTTPS URL of the video to publish (mutually
                exclusive with image_url).

        Returns:
            dict with the publish result.
        """
        return await publish_story(image_url=image_url, video_url=video_url)

    @tool
    async def publish_carousel_tool(
        items: list[dict[str, str]],
        caption: str | None = None,
    ) -> dict[str, Any]:
        """Publish an album of 2 to 10 images/videos as a carousel.

        Args:
            items: list of 2 to 10 item dicts, each with either an
                "image_url" or a "video_url" key pointing to a public HTTPS URL.
            caption: Optional caption for the carousel.

        Returns:
            dict with the publish result.
        """
        return await publish_carousel(items=items, caption=caption)

    @tool
    async def list_comments(media_id: str, limit: int = 25) -> dict[str, Any]:
        """List comments on an Instagram media object.

        Args:
            media_id: ID of the media whose comments to list.
            limit: Maximum number of comments to return (default 25).

        Returns:
            dict with the comments list, including replies.
        """
        return await graph.get(
            f"{media_id}/comments",
            fields="id,text,username,timestamp,like_count,replies{id,text,username,timestamp}",
            limit=limit,
        )

    @tool
    async def get_comment_replies(comment_id: str, limit: int = 25) -> dict[str, Any]:
        """List replies to an Instagram comment.

        Args:
            comment_id: ID of the parent comment.
            limit: Maximum number of replies to return (default 25).

        Returns:
            dict with the replies list.
        """
        return await graph.get(
            f"{comment_id}/replies",
            fields="id,text,username,timestamp,like_count",
            limit=limit,
        )

    @tool
    async def reply_to_comment(comment_id: str, message: str) -> dict[str, Any]:
        """Post a public reply to an Instagram comment.

        Args:
            comment_id: ID of the comment to reply to.
            message: Text of the reply.

        Returns:
            dict with the reply result.
        """
        return await graph.post(f"{comment_id}/replies", message=message)

    @tool
    async def hide_comment(comment_id: str, hide: bool = True) -> dict[str, Any]:
        """Hide or unhide an Instagram comment.

        Args:
            comment_id: ID of the comment to hide or unhide.
            hide: True to hide the comment, False to unhide it (default True).

        Returns:
            dict with the result.
        """
        return await graph.post(comment_id, hide=str(hide).lower())

    @tool
    async def delete_comment(comment_id: str) -> dict[str, Any]:
        """Delete an Instagram comment by ID.

        Args:
            comment_id: ID of the comment to delete.

        Returns:
            dict with the deletion result.
        """
        return await graph.delete(comment_id)

    @tool
    async def list_conversations(limit: int = 20) -> dict[str, Any]:
        """List the account's recent Instagram conversations.

        Args:
            limit: Maximum number of conversations to return (default 20).

        Returns:
            dict with the conversations list.
        """
        return await graph.get(
            f"{graph.ig_user_id()}/conversations",
            platform="instagram",
            fields="id,updated_time,participants",
            limit=limit,
        )

    @tool
    async def get_conversation(conversation_id: str, message_limit: int = 25) -> dict[str, Any]:
        """Get a single Instagram conversation and its recent messages.

        Args:
            conversation_id: ID of the conversation to fetch.
            message_limit: Maximum number of messages to return (default 25).

        Returns:
            dict with the conversation and its messages.
        """
        return await graph.get(
            conversation_id,
            fields=f"messages.limit({message_limit}){{id,created_time,from,to,message}}",
        )

    @tool
    async def send_dm(
        recipient_igsid: str,
        text: str,
        message_tag: str | None = None,
    ) -> dict[str, Any]:
        """Send a direct message to an Instagram user.

        Args:
            recipient_igsid: Instagram-scoped user ID of the recipient (igsid).
            text: Text of the direct message.
            message_tag: Optional message tag that permits sending outside the
                24h window (e.g. "GENERIC_OTP").

        Returns:
            dict with the send result.
        """
        payload: dict[str, Any] = {
            "recipient": json.dumps({"id": recipient_igsid}),
            "message": json.dumps({"text": text}),
        }
        if message_tag:
            payload["messaging_type"] = "MESSAGE_TAG"
            payload["tag"] = message_tag
        else:
            payload["messaging_type"] = "RESPONSE"
        return await graph.post(f"{graph.ig_user_id()}/messages", **payload)

    @tool
    async def get_account_insights(
        metrics: str = "reach,follower_count",
        period: str = "day",
        metric_type: str | None = None,
        since: int | None = None,
        until: int | None = None,
    ) -> dict[str, Any]:
        """Get Instagram account-level insights metrics.

        Args:
            metrics: Comma-separated metric names (default reach,follower_count).
            period: Aggregation period, e.g. day (default day).
            metric_type: Optional metric type, e.g. total_value or value.
            since: Optional start timestamp as Unix seconds.
            until: Optional end timestamp as Unix seconds.

        Returns:
            dict with the requested insights values.
        """
        return await graph.get(
            f"{graph.ig_account_id()}/insights",
            metric=metrics,
            period=period,
            metric_type=metric_type,
            since=since,
            until=until,
        )

    @tool
    async def get_media_insights(
        media_id: str,
        metrics: str = "reach,saved,likes,comments,shares",
    ) -> dict[str, Any]:
        """Get insights metrics for a single Instagram media object.

        Args:
            media_id: ID of the media to get insights for.
            metrics: Comma-separated metric names (default
                reach,saved,likes,comments,shares).

        Returns:
            dict with the requested insights values.
        """
        return await graph.get(f"{media_id}/insights", metric=metrics)
    
    @tool
    async def delete_media(media_id: str) -> dict[str, Any]:
        """Delete an Instagram media object (post, reel, or carousel).

        Args:
            media_id: ID of the media to delete.

        Returns:
            dict with the deletion result.
        """
        return await graph.delete(media_id)

