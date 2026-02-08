"""Data models for comments and analysis."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    """Sentiment classification for comments."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"
    QUESTION = "question"


class CommentAuthor(BaseModel):
    """Author information for a comment."""

    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    user_id: str


class Comment(BaseModel):
    """Single comment from TikTok/Douyin."""

    comment_id: str
    video_id: str
    text: str
    author: CommentAuthor
    like_count: int = 0
    reply_count: int = 0
    parent_comment_id: Optional[str] = None
    created_at: datetime
    is_pinned: bool = False
    sentiment: Optional[Sentiment] = None

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class CommentThread(BaseModel):
    """A thread of comments including replies."""

    main_comment: Comment
    replies: List[Comment] = Field(default_factory=list)
    total_like_count: int = 0
    total_reply_count: int = 0

    def calculate_totals(self):
        """Calculate total likes and replies including all nested replies."""
        self.total_like_count = self.main_comment.like_count + sum(
            r.like_count for r in self.replies
        )
        self.total_reply_count = self.main_comment.reply_count + len(self.replies)


class AnalysisResult(BaseModel):
    """Result of sentiment analysis and summarization."""

    comment_id: str
    sentiment: Sentiment
    confidence: float = Field(ge=0.0, le=1.0)
    key_points: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class VideoSummary(BaseModel):
    """Complete summary of a video's comments."""

    video_id: str
    total_comments: int
    comments: List[Comment]
    threads: List[CommentThread] = Field(default_factory=list)
    analysis_results: List[AnalysisResult] = Field(default_factory=list)
    overall_summary: Optional[str] = None
    sentiment_distribution: dict[str, int] = Field(default_factory=dict)

    def calculate_sentiment_distribution(self):
        """Calculate distribution of sentiments across all analyzed comments."""
        self.sentiment_distribution = {}
        for result in self.analysis_results:
            sentiment = result.sentiment.value
            self.sentiment_distribution[sentiment] = (
                self.sentiment_distribution.get(sentiment, 0) + 1
            )
