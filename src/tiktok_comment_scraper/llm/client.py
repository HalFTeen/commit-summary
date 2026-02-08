"""LLM client wrapper with fallback support."""

import json
from typing import List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from tiktok_comment_scraper.config.settings import settings
from tiktok_comment_scraper.models.comment import Comment, Sentiment

try:
    from zai import ZaiClient
    from zai.core import APIConnectionError, APIStatusError, APITimeoutError
except ImportError:
    ZaiClient = None
    APIConnectionError = Exception
    APIStatusError = Exception
    APITimeoutError = Exception


class LLMClient:
    """Client for interacting with Z.ai LLM with fallback support."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize LLM client.

        Args:
            api_key: Optional API key override
            base_url: Optional base URL override
        """
        if ZaiClient is None:
            raise ImportError(
                "zai-sdk is not installed. Install with: pip install zai-sdk"
            )

        self.api_key = api_key or settings.ZAI_API_KEY
        self.base_url = base_url or settings.ZAI_BASE_URL
        self.timeout = settings.ZAI_TIMEOUT
        self.max_retries = settings.ZAI_MAX_RETRIES
        self.model = settings.ZAI_MODEL

        self.client = ZaiClient(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
    )
    def analyze_sentiment(self, comment: Comment) -> dict:
        """Analyze sentiment of a comment using LLM.

        Args:
            comment: Comment to analyze

        Returns:
            Dictionary with sentiment, confidence, and key points
        """
        prompt = self._build_sentiment_prompt(comment)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. Analyze comments and classify them into categories. Respond with JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            result_text = response.choices[0].message.content
            return self._parse_sentiment_response(result_text)

        except (APIStatusError, APIConnectionError) as e:
            raise RuntimeError(f"LLM API error: {e}")

    def summarize_comments(self, comments: List[Comment]) -> str:
        """Summarize a list of comments.

        Args:
            comments: List of comments to summarize

        Returns:
            Summary text
        """
        comment_texts = "\n".join(
            [f"- {c.text} ({c.like_count} likes)" for c in comments]
        )

        prompt = f"""Summarize the following TikTok comments concisely. Highlight main themes, positive feedback, and common suggestions.

Comments:
{comment_texts}

Provide a 2-3 paragraph summary in Chinese."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content analysis expert. Summarize user feedback clearly and concisely.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except (APIStatusError, APIConnectionError) as e:
            raise RuntimeError(f"LLM API error: {e}")

    def batch_analyze(
        self, comments: List[Comment], batch_size: Optional[int] = None
    ) -> List[dict]:
        """Analyze multiple comments in batches.

        Args:
            comments: List of comments to analyze
            batch_size: Number of comments per batch (defaults to settings)

        Returns:
            List of analysis results
        """
        batch_size = batch_size or settings.BATCH_SIZE
        results = []

        for i in range(0, len(comments), batch_size):
            batch = comments[i : i + batch_size]
            for comment in batch:
                try:
                    result = self.analyze_sentiment(comment)
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "comment_id": comment.comment_id,
                            "sentiment": "neutral",
                            "confidence": 0.0,
                            "error": str(e),
                        }
                    )

        return results

    def _build_sentiment_prompt(self, comment: Comment) -> str:
        """Build prompt for sentiment analysis.

        Args:
            comment: Comment to analyze

        Returns:
            Prompt string
        """
        return f"""Analyze this comment and classify it. Respond with JSON in this exact format:
{{
    "sentiment": "positive|negative|neutral|suggestion|question",
    "confidence": 0.0-1.0,
    "key_points": ["point1", "point2"],
    "summary": "brief summary"
}}

Comment: "{comment.text}"
Likes: {comment.like_count}

Analyze the sentiment, confidence, extract key points, and provide a brief summary."""

    def _parse_sentiment_response(self, response_text: str) -> dict:
        """Parse LLM response to extract sentiment data.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed dictionary
        """
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            data = json.loads(response_text)

            sentiment_map = {
                "positive": Sentiment.POSITIVE,
                "negative": Sentiment.NEGATIVE,
                "neutral": Sentiment.NEUTRAL,
                "suggestion": Sentiment.SUGGESTION,
                "question": Sentiment.QUESTION,
            }

            data["sentiment"] = sentiment_map.get(data.get("sentiment", "neutral"))
            return data

        except json.JSONDecodeError:
            return {
                "sentiment": Sentiment.NEUTRAL,
                "confidence": 0.0,
                "key_points": [],
                "summary": response_text[:200],
                "error": "Failed to parse JSON response",
            }
