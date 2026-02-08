"""Test TikTok scraper."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tiktok_comment_scraper.models.comment import Comment, CommentAuthor
from tiktok_comment_scraper.scraper.tiktok import (
    TikTokAPIScraper,
    TikTokScraper,
)


@pytest.fixture
def scraper():
    """Create TikTokScraper instance."""
    return TikTokScraper(headless=True)


@pytest.fixture
def api_scraper():
    """Create TikTokAPIScraper instance."""
    return TikTokAPIScraper()


class TestTikTokScraper:
    """Test TikTokScraper class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test scraper initialization."""
        scraper = TikTokScraper(user_agent="custom_ua")
        assert scraper.user_agent == "custom_ua"
        assert scraper.headless is True

    def test_extract_video_id(self):
        """Test video ID extraction."""
        scraper = TikTokScraper(headless=True)
        video_id = scraper._extract_video_id(
            "https://www.tiktok.com/@user/video/1234567890?test=1"
        )
        assert video_id == "1234567890"

    def test_extract_video_id_invalid(self):
        """Test video ID extraction with invalid URL."""
        scraper = TikTokScraper(headless=True)
        video_id = scraper._extract_video_id("https://www.example.com/page")
        assert video_id == "unknown_video"


class TestTikTokAPIScraper:
    """Test TikTokAPIScraper class."""

    def test_initialization(self):
        """Test API scraper initialization."""
        scraper = TikTokAPIScraper(proxy_url="http://proxy.com")
        assert scraper.proxy_url == "http://proxy.com"

    def test_extract_video_id(self):
        """Test video ID extraction."""
        scraper = TikTokAPIScraper()
        video_id = scraper._extract_video_id(
            "https://www.tiktok.com/@user/video/1234567890"
        )
        assert video_id == "1234567890"

    def test_parse_comment(self):
        """Test comment parsing from API response."""
        scraper = TikTokAPIScraper()

        comment_data = {
            "cid": "comment_123",
            "text": "Great video!",
            "user": {
                "uid": "user_456",
                "unique_id": "testuser",
                "nickname": "Test User",
                "avatar_thumb": {"url_list": ["https://example.com/avatar.jpg"]},
            },
            "digg_count": 10,
            "reply_comment_total": 5,
            "reply_to_reply_id": "parent_789",
            "create_time": 1672531200,
            "is_pinned": False,
        }

        comment = scraper._parse_comment(comment_data, "video_123")

        assert comment.comment_id == "comment_123"
        assert comment.video_id == "video_123"
        assert comment.text == "Great video!"
        assert comment.author.username == "testuser"
        assert comment.author.display_name == "Test User"
        assert comment.author.user_id == "user_456"
        assert comment.like_count == 10
        assert comment.reply_count == 5
        assert comment.parent_comment_id == "parent_789"
        assert comment.is_pinned is False

    def test_parse_comment_minimal(self):
        """Test parsing comment with minimal data."""
        scraper = TikTokAPIScraper()

        comment_data = {
            "cid": "comment_123",
            "text": "Test",
            "user": {"uid": "user_456", "unique_id": "testuser"},
            "create_time": 1672531200,
        }

        comment = scraper._parse_comment(comment_data, "video_123")

        assert comment.comment_id == "comment_123"
        assert comment.like_count == 0
        assert comment.reply_count == 0
        assert comment.parent_comment_id is None
        assert comment.is_pinned is False

    @pytest.mark.asyncio
    async def test_scrape_video_comments_mock(self):
        """Test scraping with mocked HTTP client."""
        scraper = TikTokAPIScraper()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "comments": [
                {
                    "cid": "comment_1",
                    "text": "Comment 1",
                    "user": {"uid": "1", "unique_id": "user1"},
                    "digg_count": 5,
                    "create_time": 1672531200,
                }
            ],
            "cursor": "",
            "has_more": False,
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            comments = await scraper.scrape_video_comments(
                "https://www.tiktok.com/@user/video/123", max_comments=10
            )

            assert len(comments) == 1
            assert comments[0].text == "Comment 1"

    @pytest.mark.asyncio
    async def test_scrape_video_comments_error(self):
        """Test scraping with API error."""
        scraper = TikTokAPIScraper()

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=Exception("API Error"))
            MockClient.return_value = mock_client

            comments = await scraper.scrape_video_comments(
                "https://www.tiktok.com/@user/video/123"
            )

            assert len(comments) == 0

    @pytest.mark.asyncio
    async def test_scrape_video_comments_pagination(self):
        """Test scraping with pagination."""
        scraper = TikTokAPIScraper()

        responses = [
            MagicMock(
                status_code=200,
                json=lambda: {
                    "comments": [{"cid": "c1", "text": "1", "user": {"uid": "1", "unique_id": "u1"}, "create_time": 1672531200}],
                    "cursor": "cursor1",
                    "has_more": True,
                },
            ),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "comments": [{"cid": "c2", "text": "2", "user": {"uid": "2", "unique_id": "u2"}, "create_time": 1672531200}],
                    "cursor": "",
                    "has_more": False,
                },
            ),
        ]

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(side_effect=responses)
            MockClient.return_value = mock_client

            comments = await scraper.scrape_video_comments(
                "https://www.tiktok.com/@user/video/123"
            )

            assert len(comments) == 2
            assert mock_client.get.call_count == 2
