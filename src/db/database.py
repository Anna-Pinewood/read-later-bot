"""
Database operations for the ReadLater bot.
"""
import logging
from typing import Dict, List, Any, Optional
import asyncpg

from consts import (
    POSTGRES_USER, POSTGRES_PASSWORD,
    POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT
)

logger = logging.getLogger(__name__)


class Database:
    """Database connection and operations."""

    def __init__(self):
        """Initialize database connection pool."""
        self.pool = None

    async def connect(self):
        """Create a connection pool to the database."""
        try:
            self.pool = await asyncpg.create_pool(
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error("Error connecting to database: %s", e)
            raise

    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")

    # Content Item operations

    async def add_content_item(self,
                               user_id: int,
                               content: str,
                               source: str,
                               message_id: int | None = None,
                               chat_id: int | None = None,
                               content_type: str | None = None) -> int:
        """
        Add a new content item to the database.

        Args:
            user_id: Telegram user ID
            content: Content text or link
            source: Source of the content (@username or @channel)
            message_id: Optional message ID for forwarded messages
            chat_id: Optional chat ID for forwarded messages
            content_type: Optional content type (video, text, etc.)

        Returns:
            int: ID of the created content item
        """
        async with self.pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO content_items 
                    (user_id, content, source, message_id, chat_id, content_type)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """
                item_id = await conn.fetchval(
                    query, user_id, content, source, message_id, chat_id, content_type
                )
                logger.info("Added new content item (id=%s) for user %s", item_id, user_id)
                return item_id
            except Exception as e:
                logger.error("Error adding content item for user %s: %s", user_id, e)
                raise

    async def update_content_type(self, content_id: int, content_type: str) -> bool:
        """
        Update the content type of an item.

        Args:
            content_id: Content item ID
            content_type: New content type (video, text, etc.)

        Returns:
            bool: Success status
        """
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE content_items
                    SET content_type = $1
                    WHERE id = $2
                """
                await conn.execute(query, content_type, content_id)
                logger.info("Updated content type to '%s' for item %s", content_type, content_id)
                return True
            except Exception as e:
                logger.error("Error updating content type for item %s: %s", content_id, e)
                return False

    async def update_content_status(self, content_id: int, status: str) -> bool:
        """
        Update the status of a content item.

        Args:
            content_id: Content item ID
            status: New status ('unread' or 'processed')

        Returns:
            bool: Success status
        """
        async with self.pool.acquire() as conn:
            try:
                # Use a parameterized query with explicit type casting for the status
                query = """
                    UPDATE content_items
                    SET status = $1::VARCHAR,
                        date_read = CASE WHEN $1::VARCHAR = 'processed' THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE id = $2
                """
                await conn.execute(query, status, content_id)
                logger.info("Updated status to '%s' for item %s", status, content_id)
                return True
            except Exception as e:
                logger.error("Error updating status for item %s: %s", content_id, e)
                return False

    async def get_last_content_item(self,
                                    user_id: int,
                                    content_type: str | None = None) -> Dict[str, Any] | None:
        """
        Get the last added content item for a user.

        Args:
            user_id: Telegram user ID
            content_type: Optional filter by content type

        Returns:
            Dict or None: Content item data or None if not found
        """
        async with self.pool.acquire() as conn:
            try:
                if content_type:
                    query = """
                        SELECT * FROM content_items
                        WHERE user_id = $1 AND content_type = $2
                        ORDER BY date_added DESC
                        LIMIT 1
                    """
                    record = await conn.fetchrow(query, user_id, content_type)
                    logger.info("Retrieved last %s content for user %s", content_type, user_id)
                else:
                    query = """
                        SELECT * FROM content_items
                        WHERE user_id = $1
                        ORDER BY date_added DESC
                        LIMIT 1
                    """
                    record = await conn.fetchrow(query, user_id)
                    logger.info("Retrieved last content item for user %s", user_id)

                if record:
                    return dict(record)
                return None
            except Exception as e:
                logger.error("Error getting last content item for user %s: %s", user_id, e)
                return None

    async def get_random_content_item(self,
                                      user_id: int,
                                      content_type: str | None = None) -> Dict[str, Any] | None:
        """
        Get a random unread content item for a user.

        Args:
            user_id: Telegram user ID
            content_type: Optional filter by content type

        Returns:
            Dict or None: Content item data or None if not found
        """
        async with self.pool.acquire() as conn:
            try:
                if content_type:
                    query = """
                        SELECT * FROM content_items
                        WHERE user_id = $1 AND status = 'unread' AND content_type = $2
                        ORDER BY RANDOM()
                        LIMIT 1
                    """
                    record = await conn.fetchrow(query, user_id, content_type)
                    logger.info("Retrieved random unread %s content for user %s", content_type, user_id)
                else:
                    query = """
                        SELECT * FROM content_items
                        WHERE user_id = $1 AND status = 'unread'
                        ORDER BY RANDOM()
                        LIMIT 1
                    """
                    record = await conn.fetchrow(query, user_id)
                    logger.info("Retrieved random unread content item for user %s", user_id)

                if record:
                    return dict(record)
                return None
            except Exception as e:
                logger.error("Error getting random content item for user %s: %s", user_id, e)
                return None

    async def delete_content_item(self, content_id: int) -> bool:
        """
        Delete a content item and its tag associations.

        Args:
            content_id: Content item ID

        Returns:
            bool: Success status
        """
        async with self.pool.acquire() as conn:
            try:
                # Begin a transaction
                async with conn.transaction():
                    # The content_item_tags references will be automatically deleted due to CASCADE
                    query = "DELETE FROM content_items WHERE id = $1"
                    await conn.execute(query, content_id)

                logger.info("Deleted content item %s", content_id)
                return True
            except Exception as e:
                logger.error("Error deleting content item %s: %s", content_id, e)
                return False

    # Tag operations

    async def get_user_tags(self, user_id: int) -> list[Dict[str, Any]]:
        """
        Get all tags for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            List of tag objects
        """
        async with self.pool.acquire() as conn:
            try:
                query = "SELECT id, name FROM tags WHERE user_id = $1 ORDER BY name"
                records = await conn.fetch(query, user_id)
                return [dict(record) for record in records]
            except Exception as e:
                logger.error("Error getting tags for user %s: %s", user_id, e)
                return []

    async def add_tag(self, user_id: int, tag_name: str) -> int:
        """
        Add a new tag or get existing one.

        Args:
            user_id: Telegram user ID
            tag_name: Name of the tag to add

        Returns:
            int: ID of the tag
        """
        async with self.pool.acquire() as conn:
            try:
                # Check if tag already exists
                query = "SELECT id FROM tags WHERE user_id = $1 AND name = $2"
                tag_id = await conn.fetchval(query, user_id, tag_name)

                if tag_id:
                    logger.info("Tag '%s' already exists for user %s", tag_name, user_id)
                    return tag_id

                # Create new tag
                query = """
                    INSERT INTO tags (user_id, name)
                    VALUES ($1, $2)
                    RETURNING id
                """
                tag_id = await conn.fetchval(query, user_id, tag_name)
                logger.info("Created new tag '%s' (id=%s) for user %s", tag_name, tag_id, user_id)
                return tag_id
            except Exception as e:
                logger.error("Error adding tag '%s' for user %s: %s", tag_name, user_id, e)
                raise

    async def add_tag_to_content(self, content_id: int, tag_id: int) -> bool:
        """
        Associate a tag with a content item.

        Args:
            content_id: Content item ID
            tag_id: Tag ID

        Returns:
            bool: Success status
        """
        async with self.pool.acquire() as conn:
            try:
                # Check if association already exists
                check_query = """
                    SELECT 1 FROM content_item_tags
                    WHERE content_item_id = $1 AND tag_id = $2
                """
                exists = await conn.fetchval(check_query, content_id, tag_id)

                if exists:
                    logger.info("Tag (id=%s) already associated with content item %s", tag_id, content_id)
                    return True

                # Create association
                query = """
                    INSERT INTO content_item_tags (content_item_id, tag_id)
                    VALUES ($1, $2)
                """
                await conn.execute(query, content_id, tag_id)
                logger.info("Associated tag (id=%s) with content item %s", tag_id, content_id)
                return True
            except Exception as e:
                logger.error("Error associating tag (id=%s) with content item %s: %s", tag_id, content_id, e)
                return False

    async def get_content_by_tags(self,
                                  user_id: int,
                                  tags: list[int],
                                  relation: str = "and") -> list[Dict[str, Any]]:
        """
        Get content items by tags.

        Args:
            user_id: Telegram user ID
            tags: List of tag IDs
            relation: Relation between tags - "and" (all tags) or "or" (any tag)

        Returns:
            List of content items
        """
        if not tags:
            return []

        async with self.pool.acquire() as conn:
            try:
                if relation.lower() == "and":
                    # Get items that have ALL the specified tags
                    query = """
                        SELECT ci.* FROM content_items ci
                        WHERE ci.user_id = $1 AND ci.id IN (
                            SELECT cit.content_item_id
                            FROM content_item_tags cit
                            WHERE cit.tag_id = ANY($2::int[])
                            GROUP BY cit.content_item_id
                            HAVING COUNT(DISTINCT cit.tag_id) = $3
                        )
                        ORDER BY ci.date_added DESC
                    """
                    records = await conn.fetch(query, user_id, tags, len(tags))
                    logger.info("Retrieved %s content items with ALL tags %s for user %s",
                                len(records), tags, user_id)
                else:
                    # Get items that have ANY of the specified tags
                    query = """
                        SELECT DISTINCT ci.* FROM content_items ci
                        JOIN content_item_tags cit ON ci.id = cit.content_item_id
                        WHERE ci.user_id = $1 AND cit.tag_id = ANY($2::int[])
                        ORDER BY ci.date_added DESC
                    """
                    records = await conn.fetch(query, user_id, tags)
                    logger.info("Retrieved %s content items with ANY tags %s for user %s",
                                len(records), tags, user_id)

                return [dict(record) for record in records]
            except Exception as e:
                logger.error("Error getting content by tags %s for user %s: %s", tags, user_id, e)
                return []

    # Statistics operations

    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get reading statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict: Statistics data
        """
        async with self.pool.acquire() as conn:
            try:
                stats = {}

                # Total counts
                count_query = """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'unread') as unread,
                        COUNT(*) FILTER (WHERE status = 'processed') as read
                    FROM content_items 
                    WHERE user_id = $1
                """
                counts = await conn.fetchrow(count_query, user_id)
                stats["total"] = counts["total"]
                stats["unread"] = counts["unread"]
                stats["read"] = counts["read"]

                # Read last week
                week_query = """
                    SELECT COUNT(*) 
                    FROM content_items 
                    WHERE user_id = $1 
                      AND status = 'processed' 
                      AND date_read > CURRENT_TIMESTAMP - INTERVAL '7 days'
                """
                stats["read_last_week"] = await conn.fetchval(week_query, user_id)

                # Read last month
                month_query = """
                    SELECT COUNT(*) 
                    FROM content_items 
                    WHERE user_id = $1 
                      AND status = 'processed' 
                      AND date_read > CURRENT_TIMESTAMP - INTERVAL '30 days'
                """
                stats["read_last_month"] = await conn.fetchval(month_query, user_id)

                # Content type distribution
                type_query = """
                    SELECT content_type, COUNT(*) 
                    FROM content_items 
                    WHERE user_id = $1 AND content_type IS NOT NULL
                    GROUP BY content_type
                """
                type_records = await conn.fetch(type_query, user_id)
                stats["content_types"] = {record["content_type"]: record["count"] for record in type_records}

                logger.info("Retrieved statistics for user %s", user_id)
                return stats
            except Exception as e:
                logger.error("Error getting statistics for user %s: %s", user_id, e)
                return {"total": 0, "unread": 0, "read": 0, "read_last_week": 0, "read_last_month": 0}


# Create a singleton instance
db = Database()
