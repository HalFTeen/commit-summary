"""Test LLM client."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tiktok_comment_scraper.llm.client import LLMClient
from tiktok_comment_scraper.models.comment import (
    Comment,
    CommentAuthor,
    Sentiment,
)


@pytest.fixture
def mock_client():
    """Create mock LLM client."""
    with patch("tiktok_comment_scraper.llm.client.ZaiClient"):
        client = LLMClient(api_key="test_key")
        client.client = MagicMock()
        return client


@pytest.fixture
def sample_comment():
    """Create sample comment for testing."""
    author = CommentAuthor(username="testuser", user_id="123")
    return Comment(
        comment_id="c1",
        video_id="v1",
        text="This is a great video!",
        author=author,
        created_at=datetime.now(),
        like_count=10,
    )


class TestLLMClient:
    """Test LLMClient class."""

    def test_initialization(self):
        """Test client initialization."""
        with patch("tiktok_comment_scraper.llm.client.ZaiClient"):
            client = LLMClient(api_key="test_key", base_url="https://test.com")
            assert client.api_key == "test_key"
            assert client.base_url == "https://test.com"
            assert client.model == "glm-4.7"

    def test_import_error_without_sdk(self):
        """Test that ImportError is raised without SDK."""
        with patch("tiktok_comment_scraper.llm.client.ZaiClient", None):
            with pytest.raises(ImportError):
                LLMClient(api_key="test_key")

    def test_analyze_sentiment_success(self, mock_client, sample_comment):
        """Test successful sentiment analysis."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''{
    "sentiment": "positive",
    "confidence": 0.95,
    "key_points": ["Great video", "Helpful content"],
    "summary": "User enjoyed the video"
}'''
        mock_client.client.chat.completions.create.return_value = mock_response

        result = mock_client.analyze_sentiment(sample_comment)

        assert result["sentiment"] == Sentiment.POSITIVE
        assert result["confidence"] == 0.95
        assert len(result["key_points"]) == 2
        assert result["summary"] == "User enjoyed the video"

    def test_analyze_sentiment_with_json_code_block(self, mock_client, sample_comment):
        """Test parsing sentiment from JSON code block."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''```json
{
    "sentiment": "positive",
    "confidence": 0.95,
    "key_points": ["Great"],
    "summary": "Good"
}
```'''
        mock_client.client.chat.completions.create.return_value = mock_response

        result = mock_client.analyze_sentiment(sample_comment)

        assert result["sentiment"] == Sentiment.POSITIVE
        assert result["confidence"] == 0.95

    def test_analyze_sentiment_json_parse_error(self, mock_client, sample_comment):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Not valid JSON"
        mock_client.client.chat.completions.create.return_value = mock_response

        result = mock_client.analyze_sentiment(sample_comment)

        assert result["sentiment"] == Sentiment.NEUTRAL
        assert result["confidence"] == 0.0
        assert "error" in result

    def test_summarize_comments(self, mock_client, sample_comment):
        """Test comment summarization."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "这是一段评论摘要..."
        mock_client.client.chat.completions.create.return_value = mock_response

        summary = mock_client.summarize_comments([sample_comment])

        assert summary == "这是一段评论摘要..."
        mock_client.client.chat.completions.create.assert_called_once()

    def test_batch_analyze(self, mock_client):
        """Test batch analysis of comments."""
        author = CommentAuthor(username="testuser", user_id="123")
        comments = [
            Comment(
                comment_id=f"c{i}",
                video_id="v1",
                text=f"Comment {i}",
                author=author,
                created_at=datetime.now(),
            )
            for i in range(3)
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''{
    "sentiment": "neutral",
    "confidence": 0.8,
    "key_points": [],
    "summary": "Comment"
}'''
        mock_client.client.chat.completions.create.return_value = mock_response

        with patch.object(mock_client, "analyze_sentiment") as mock_analyze:
            mock_analyze.return_value = {
                "sentiment": Sentiment.NEUTRAL,
                "confidence": 0.8,
                "key_points": [],
            }
            results = mock_client.batch_analyze(comments, batch_size=2)

            assert len(results) == 3
            assert mock_analyze.call_count == 3

    def test_batch_analyze_with_error(self, mock_client, sample_comment):
        """Test batch analysis with error handling."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''{
    "sentiment": "neutral",
    "confidence": 0.8,
    "key_points": [],
    "summary": "Comment"
}'''
        mock_client.client.chat.completions.create.return_value = mock_response

        with patch.object(
            mock_client, "analyze_sentiment", side_effect=RuntimeError("API Error")
        ):
            results = mock_client.batch_analyze([sample_comment])

            assert len(results) == 1
            assert "error" in results[0]

    def test_retry_on_timeout(self, mock_client, sample_comment):
        """Test retry logic on timeout."""
        from zai.core import APITimeoutError

        mock_client.client.chat.completions.create.side_effect = [
            APITimeoutError("Timeout"),
            APITimeoutError("Timeout"),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content='''{
    "sentiment": "neutral",
    "confidence": 0.8,
    "key_points": [],
    "summary": "Comment"
}'''
                        )
                    )
                ]
            ),
        ]

        result = mock_client.analyze_sentiment(sample_comment)

        assert result["sentiment"] == Sentiment.NEUTRAL
        assert mock_client.client.chat.completions.create.call_count == 3
