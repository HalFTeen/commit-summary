"""TikTok/Douyin comment scraper with anti-detection."""

import asyncio
import json
import random
import time
from typing import List, Optional

import httpx
from fake_useragent import UserAgent
from playwright.async_api import async_playwright

from tiktok_comment_scraper.config.settings import settings
from tiktok_comment_scraper.models.comment import Comment, CommentAuthor


class TikTokScraper:
    """Scraper for TikTok/Douyin comments with anti-detection."""

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        headless: bool = True,
    ):
        """Initialize TikTok scraper.

        Args:
            proxy_url: Optional proxy URL (format: http://user:pass@host:port)
            user_agent: Optional custom user agent
            headless: Run browser in headless mode
        """
        self.proxy_url = proxy_url or settings.PROXY_URL
        self.user_agent = user_agent or settings.USER_AGENT
        if not self.user_agent:
            self.user_agent = UserAgent().random

        self.headless = headless
        self.timeout = settings.TIKTOK_TIMEOUT
        self.max_retries = settings.TIKTOK_MAX_RETRIES
        self.request_delay = settings.TIKTOK_REQUEST_DELAY

        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_browser()

    async def _initialize_browser(self):
        """Initialize Playwright browser with anti-detection."""
        self.playwright = await async_playwright().start()

        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]

        launch_options = {
            "headless": self.headless,
            "args": browser_args,
        }

        if self.proxy_url:
            launch_options["proxy"] = {"server": self.proxy_url}

        self.browser = await self.playwright.chromium.launch(**launch_options)

        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def _close_browser(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_video_comments(
        self, video_url: str, max_comments: Optional[int] = None
    ) -> List[Comment]:
        """Scrape all comments from a TikTok/Douyin video.

        Args:
            video_url: URL of the TikTok/Douyin video
            max_comments: Maximum number of comments to fetch (None for all)

        Returns:
            List of Comment objects
        """
        try:
            page = await self.context.new_page()

            await self._navigate_with_retry(page, video_url)

            await page.wait_for_timeout(2000)

            comments = []
            page.goto(video_url)

            last_comment_count = 0
            consecutive_no_new = 0
            max_consecutive = 5

            while True:
                if max_comments and len(comments) >= max_comments:
                    break

                await self._scroll_comments(page)

                new_comments = await self._extract_comments(page, comments)
                comments.extend(new_comments)

                print(f"Scraped {len(comments)} comments...")

                if len(new_comments) == 0:
                    consecutive_no_new += 1
                    if consecutive_no_new >= max_consecutive:
                        break
                else:
                    consecutive_no_new = 0

                await page.wait_for_timeout(random.randint(1000, 2000))

            await page.close()
            return comments

        except Exception as e:
            raise RuntimeError(f"Error scraping comments: {e}")

    async def _navigate_with_retry(self, page, url: str):
        """Navigate to URL with retry logic."""
        for attempt in range(self.max_retries):
            try:
                await page.goto(url, timeout=self.timeout * 1000)
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def _scroll_comments(self, page):
        """Scroll to load more comments."""
        selectors = [
            'div[data-e2e="comment-list"]',
            'div[class*="comment"]',
            '[class*="CommentsList"]',
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    await element.scroll_into_view_if_needed()
                    break
            except:
                continue

        await page.keyboard.press("PageDown")
        await page.wait_for_timeout(500)

    async def _extract_comments(
        self, page, existing_comments: List[Comment]
    ) -> List[Comment]:
        """Extract comments from current page state."""
        new_comments = []

        try:
            content = await page.content()
            comment_data = await page.evaluate("""() => {
                const comments = [];
                const commentElements = document.querySelectorAll('[class*="comment"], [data-e2e*="comment"]');
                
                commentElements.forEach(el => {
                    try {
                        const textEl = el.querySelector('[class*="text"], [class*="content"]');
                        const authorEl = el.querySelector('[class*="author"], [class*="user"]');
                        const likeEl = el.querySelector('[class*="like"]');
                        
                        if (textEl && authorEl) {
                            comments.push({
                                text: textEl.textContent?.trim() || '',
                                author: authorEl.textContent?.trim() || 'Anonymous',
                                likes: likeEl ? parseInt(likeEl.textContent) || 0 : 0
                            });
                        }
                    } catch (e) {
                        console.error('Error extracting comment:', e);
                    }
                });
                
                return comments;
            }""")

            video_id = self._extract_video_id(page.url)

            for idx, data in enumerate(comment_data):
                comment_id = f"{video_id}_comment_{len(existing_comments) + idx}"

                if any(c.comment_id == comment_id for c in existing_comments):
                    continue

                author = CommentAuthor(
                    username=data.get("author", "anonymous"),
                    user_id=f"user_{hash(data.get('author', '')) % 1000000}",
                )

                from datetime import datetime

                comment = Comment(
                    comment_id=comment_id,
                    video_id=video_id,
                    text=data.get("text", ""),
                    author=author,
                    like_count=data.get("likes", 0),
                    created_at=datetime.now(),
                )

                new_comments.append(comment)

        except Exception as e:
            print(f"Error extracting comments: {e}")

        return new_comments

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        try:
            if "/video/" in url:
                return url.split("/video/")[-1].split("?")[0]
            return "unknown_video"
        except:
            return "unknown_video"


class TikTokAPIScraper:
    """Alternative scraper using TikTok hidden API (more efficient but less stable)."""

    def __init__(self, proxy_url: Optional[str] = None):
        """Initialize API scraper.

        Args:
            proxy_url: Optional proxy URL
        """
        self.proxy_url = proxy_url or settings.PROXY_URL
        self.timeout = settings.TIKTOK_TIMEOUT
        self.base_url = "https://www.tiktok.com"

    async def scrape_video_comments(
        self, video_url: str, max_comments: Optional[int] = None
    ) -> List[Comment]:
        """Scrape comments using hidden API.

        Args:
            video_url: Video URL
            max_comments: Maximum comments to fetch

        Returns:
            List of Comment objects
        """
        video_id = self._extract_video_id(video_url)

        proxies = {"http://": self.proxy_url, "https://": self.proxy_url} if self.proxy_url else None

        async with httpx.AsyncClient(proxies=proxies, timeout=self.timeout) as client:
            comments = []
            cursor = "0"

            while True:
                if max_comments and len(comments) >= max_comments:
                    break

                try:
                    response = await client.get(
                        f"{self.base_url}/api/comment/list/",
                        params={
                            "aweme_id": video_id,
                            "count": 20,
                            "cursor": cursor,
                        },
                        headers={
                            "User-Agent": UserAgent().random,
                            "Referer": video_url,
                        },
                    )

                    if response.status_code != 200:
                        break

                    data = response.json()

                    if not data.get("comments"):
                        break

                    for comment_data in data["comments"]:
                        comment = self._parse_comment(comment_data, video_id)
                        comments.append(comment)

                    cursor = data.get("cursor", "")
                    if not cursor or data.get("has_more", False) is False:
                        break

                    await asyncio.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    print(f"Error fetching comments: {e}")
                    break

            return comments

    def _parse_comment(self, data: dict, video_id: str) -> Comment:
        """Parse comment data from API response."""
        from datetime import datetime

        comment_id = data.get("cid", "")

        author_data = data.get("user", {})
        author = CommentAuthor(
            username=author_data.get("unique_id", "anonymous"),
            display_name=author_data.get("nickname"),
            user_id=str(author_data.get("uid", "")),
            avatar_url=author_data.get("avatar_thumb", {}).get("url_list", [""])[0],
        )

        return Comment(
            comment_id=comment_id,
            video_id=video_id,
            text=data.get("text", ""),
            author=author,
            like_count=data.get("digg_count", 0),
            reply_count=data.get("reply_comment_total", 0),
            parent_comment_id=data.get("reply_to_reply_id"),
            created_at=datetime.fromtimestamp(data.get("create_time", time.time())),
            is_pinned=data.get("is_pinned", False),
        )

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        if "/video/" in url:
            return url.split("/video/")[-1].split("?")[0]
        return ""
