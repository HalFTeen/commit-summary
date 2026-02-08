"""Test comment data models."""

from datetime import datetime

import pytest

from tiktok_comment_scraper.models.comment import (
    AnalysisResult,
    Comment,
    CommentAuthor,
    CommentThread,
    Sentiment,
    VideoSummary,
)


class TestCommentAuthor:
    """Test CommentAuthor model."""

    def test_create_author_minimal(self):
        """Test creating author with minimal data."""
        author = CommentAuthor(username="testuser", user_id="123")
        assert author.username == "testuser"
        assert author.user_id == "123"
        assert author.display_name is None
        assert author.avatar_url is None

    def test_create_author_full(self):
        """Test creating author with all fields."""
        author = CommentAuthor(
            username="testuser",
            display_name="Test User",
            avatar_url="https://example.com/avatar.jpg",
            user_id="123",
        )
        assert author.username == "testuser"
        assert author.display_name == "Test User"
        assert author.avatar_url == "https://example.com/avatar.jpg"


class TestComment:
    """Test Comment model."""

    def test_create_comment_minimal(self):
        """Test creating comment with minimal data."""
        author = CommentAuthor(username="testuser", user_id="123")
        comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Test comment",
            author=author,
            created_at=datetime.now(),
        )
        assert comment.comment_id == "c1"
        assert comment.text == "Test comment"
        assert comment.like_count == 0
        assert comment.reply_count == 0
        assert comment.sentiment is None

    def test_create_comment_with_parent(self):
        """Test creating reply comment with parent."""
        author = CommentAuthor(username="testuser", user_id="123")
        comment = Comment(
            comment_id="c2",
            video_id="v1",
            text="Reply",
            author=author,
            created_at=datetime.now(),
            parent_comment_id="c1",
        )
        assert comment.parent_comment_id == "c1"

    def test_set_sentiment(self):
        """Test setting sentiment on comment."""
        author = CommentAuthor(username="testuser", user_id="123")
        comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Great video!",
            author=author,
            created_at=datetime.now(),
            sentiment=Sentiment.POSITIVE,
        )
        assert comment.sentiment == Sentiment.POSITIVE


class TestCommentThread:
    """Test CommentThread model."""

    def test_create_thread_empty(self):
        """Test creating thread without replies."""
        author = CommentAuthor(username="testuser", user_id="123")
        main_comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Main comment",
            author=author,
            created_at=datetime.now(),
            like_count=10,
            reply_count=2,
        )
        thread = CommentThread(main_comment=main_comment)
        assert thread.main_comment.comment_id == "c1"
        assert len(thread.replies) == 0

    def test_create_thread_with_replies(self):
        """Test creating thread with replies."""
        author = CommentAuthor(username="testuser", user_id="123")
        main_comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Main comment",
            author=author,
            created_at=datetime.now(),
            like_count=10,
        )
        reply1 = Comment(
            comment_id="r1",
            video_id="v1",
            text="Reply 1",
            author=author,
            created_at=datetime.now(),
            like_count=5,
            parent_comment_id="c1",
        )
        reply2 = Comment(
            comment_id="r2",
            video_id="v1",
            text="Reply 2",
            author=author,
            created_at=datetime.now(),
            like_count=3,
            parent_comment_id="c1",
        )
        thread = CommentThread(main_comment=main_comment, replies=[reply1, reply2])
        assert len(thread.replies) == 2

    def test_calculate_totals(self):
        """Test calculating total likes and replies."""
        author = CommentAuthor(username="testuser", user_id="123")
        main_comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Main comment",
            author=author,
            created_at=datetime.now(),
            like_count=10,
            reply_count=5,
        )
        reply1 = Comment(
            comment_id="r1",
            video_id="v1",
            text="Reply 1",
            author=author,
            created_at=datetime.now(),
            like_count=5,
            parent_comment_id="c1",
        )
        thread = CommentThread(main_comment=main_comment, replies=[reply1])
        thread.calculate_totals()
        assert thread.total_like_count == 15
        assert thread.total_reply_count == 6


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_create_result(self):
        """Test creating analysis result."""
        result = AnalysisResult(
            comment_id="c1",
            sentiment=Sentiment.POSITIVE,
            confidence=0.95,
            key_points=["Great content", "Helpful"],
            summary="User liked the content",
        )
        assert result.comment_id == "c1"
        assert result.sentiment == Sentiment.POSITIVE
        assert result.confidence == 0.95
        assert len(result.key_points) == 2

    def test_confidence_bounds(self):
        """Test that confidence must be between 0 and 1."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnalysisResult(comment_id="c1", sentiment=Sentiment.POSITIVE, confidence=1.5)


class TestVideoSummary:
    """Test VideoSummary model."""

    def test_create_summary(self):
        """Test creating video summary."""
        author = CommentAuthor(username="testuser", user_id="123")
        comment = Comment(
            comment_id="c1",
            video_id="v1",
            text="Test",
            author=author,
            created_at=datetime.now(),
        )
        summary = VideoSummary(video_id="v1", total_comments=1, comments=[comment])
        assert summary.video_id == "v1"
        assert summary.total_comments == 1
        assert len(summary.comments) == 1

    def test_sentiment_distribution(self):
        """Test calculating sentiment distribution."""
        author = CommentAuthor(username="testuser", user_id="123")
        comment1 = Comment(
            comment_id="c1",
            video_id="v1",
            text="Great",
            author=author,
            created_at=datetime.now(),
        )
        comment2 = Comment(
            comment_id="c2",
            video_id="v1",
            text="Bad",
            author=author,
            created_at=datetime.now(),
        )
        summary = VideoSummary(
            video_id="v1", total_comments=2, comments=[comment1, comment2]
        )
        summary.analysis_results = [
            AnalysisResult(comment_id="c1", sentiment=Sentiment.POSITIVE, confidence=0.9),
            AnalysisResult(comment_id="c2", sentiment=Sentiment.NEGATIVE, confidence=0.8),
        ]
        summary.calculate_sentiment_distribution()
        assert summary.sentiment_distribution["positive"] == 1
        assert summary.sentiment_distribution["negative"] == 1
