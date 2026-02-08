"""Advanced Douyin comment scraper with robust extraction."""

import asyncio
import json
import re
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fake_useragent import UserAgent
from playwright.async_api import async_playwright


class DouyinScraperPro:
    """Professional Douyin comment scraper with advanced features."""

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        headless: bool = False,
        timeout: int = 60,
    ):
        """Initialize advanced scraper.

        Args:
            proxy_url: Optional proxy URL
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
        """
        self.proxy_url = proxy_url
        self.headless = headless
        self.timeout = timeout * 1000  # Convert to ms
        self.user_agent = UserAgent().random
        self.comments = []
        self.seen_hashes = set()  # Track seen comments to avoid duplicates

    async def scrape(self, video_url: str, max_comments: Optional[int] = None) -> dict:
        """Scrape Douyin comments with full pipeline.

        Args:
            video_url: Douyin video URL
            max_comments: Maximum comments to scrape (None for all)

        Returns:
            Dictionary with scraping results
        """
        print("=" * 70)
        print("🔍 抖音高级评论爬虫")
        print("=" * 70)
        print(f"\n📍 目标URL: {video_url}")
        print(f"🎥 视频ID: {self._extract_video_id(video_url)}")
        print(f"🌐 用户代理: {self.user_agent[:50]}...")
        print(f"🖥️  无头模式: {'是' if self.headless else '否'}")

        try:
            async with async_playwright() as p:
                # Launch browser with advanced options
                browser_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--start-maximized",
                ]

                launch_options = {
                    "headless": self.headless,
                    "args": browser_args,
                    "slow_mo": 50,  # Slow down operations
                }

                if self.proxy_url:
                    launch_options["proxy"] = {"server": self.proxy_url}

                print("\n🚀 启动浏览器...")
                browser = await p.chromium.launch(**launch_options)

                # Create context with realistic settings
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                    permissions=["geolocation"],
                    geolocation={"latitude": 39.9042, "longitude": 116.4074},  # Beijing
                    color_scheme="light",
                    device_scale_factor=1,
                )

                # Inject anti-detection scripts
                await context.add_init_script("""
                    // Hide webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Mock Chrome object
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // Mock permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );

                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en']
                    });
                """)

                page = await context.new_page()

                # Set up console logging
                page.on("console", lambda msg: print(f"🔧 [浏览器] {msg.text}"))

                print("📄 正在加载页面...")
                try:
                    await page.goto(video_url, timeout=self.timeout, wait_until="networkidle")
                except Exception as e:
                    print(f"⚠️  页面加载超时，继续尝试...")
                    await page.wait_for_timeout(5000)

                # Wait for page to stabilize
                await page.wait_for_timeout(random.randint(3000, 5000))

                # Check if we need to handle any popups or verifications
                await self._handle_page_elements(page)

                # Scroll to find and load comments
                print("\n🔄 开始滚动和加载评论...")
                scroll_attempts = 0
                max_scrolls = 100
                consecutive_empty = 0

                while scroll_attempts < max_scrolls:
                    if max_comments and len(self.comments) >= max_comments:
                        print(f"\n✅ 已达到目标评论数: {max_comments}")
                        break

                    # Extract comments from current view
                    new_comments = await self._extract_comments_advanced(page)
                    if new_comments:
                        old_count = len(self.comments)
                        self.comments.extend(new_comments)
                        new_count = len(self.comments)
                        consecutive_empty = 0
                        print(f"📝 第{scroll_attempts + 1}次滚动: +{new_count - old_count} 条 (总计: {new_count})")
                    else:
                        consecutive_empty += 1
                        print(f"⏸️  第{scroll_attempts + 1}次滚动: 无新评论")

                        if consecutive_empty >= 5:
                            print("\nℹ️  连续多次无新评论，可能已到底部")
                            break

                    # Scroll down
                    await self._smart_scroll(page)
                    await page.wait_for_timeout(random.randint(1500, 2500))

                    scroll_attempts += 1

                await browser.close()

                # Prepare results
                video_id = self._extract_video_id(video_url)

                result = {
                    "video_url": video_url,
                    "video_id": video_id,
                    "total_comments": len(self.comments),
                    "comments": self.comments,
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "1.0.0",
                    "success": len(self.comments) > 0,
                }

                # Save results
                output_file = Path("output") / f"douyin_{video_id}_{int(datetime.now().timestamp())}.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                # Display summary
                self._print_summary(result, output_file)

                return result

        except Exception as e:
            print(f"\n❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def _handle_page_elements(self, page):
        """Handle any popups, cookies, or verification elements."""
        print("🔎 检查页面元素...")

        # Try to find and click on any cookie consent
        cookie_selectors = [
            'button[class*="cookie"]',
            'button[class*="accept"]',
            'div[class*="cookie"] button',
            '[role="dialog"] button',
        ]

        for selector in cookie_selectors:
            try:
                elements = await page.locator(selector).all()
                if elements:
                    print(f"✓ 找到cookie按钮，尝试点击: {selector}")
                    for element in elements[:1]:
                        await element.click()
                        await page.wait_for_timeout(1000)
                    break
            except:
                continue

    async def _smart_scroll(self, page):
        """Perform smart scrolling to load content."""
        try:
            # Get current scroll position
            scroll_height = await page.evaluate("document.body.scrollHeight")

            # Scroll to near bottom
            await page.evaluate(f"window.scrollTo(0, {scroll_height - 500})")

            # Wait for new content
            await page.wait_for_timeout(500)

        except Exception as e:
            print(f"⚠️  滚动错误: {e}")
            try:
                # Fallback: use keyboard
                await page.keyboard.press("End")
                await page.wait_for_timeout(1000)
            except:
                pass

    async def _extract_comments_advanced(self, page) -> List[dict]:
        """Advanced comment extraction with multiple strategies."""
        new_comments = []

        try:
            # Strategy 1: Try to find comment containers
            comment_selectors = [
                'div[class*="comment-list"] > div',
                'div[class*="CommentItem"]',
                'div[class*="commentItem"]',
                'div[class*="reply-item"]',
                '[class*="CommentContainer"] > div',
                'li[class*="comment"]',
            ]

            all_text_content = await page.evaluate("""() => {
                const results = [];

                // Find all text elements that might be comments
                const allElements = document.querySelectorAll('*');

                for (let el of allElements) {
                    // Check if element contains text
                    const text = el.textContent?.trim();
                    if (!text || text.length < 2 || text.length > 1000) continue;

                    // Check if it looks like a comment text
                    const parent = el.parentElement;
                    if (!parent) continue;

                    // Check for common comment indicators
                    const hasLikeButton = parent.querySelector('[class*="like"], [class*="digg"], [class*="thumb"]');
                    const hasReplyButton = parent.querySelector('[class*="reply"], [class*="comment"]');
                    const isInCommentSection = parent.closest('[class*="comment"], [class*="Comment"]');

                    if (hasLikeButton || hasReplyButton || isInCommentSection) {
                        // Get parent element
                        const commentContainer = el.closest('[class*="comment"], [class*="Comment"], [class*="item"]');

                        if (commentContainer) {
                            // Try to extract likes
                            let likes = 0;
                            const likeElements = commentContainer.querySelectorAll('[class*="like"], [class*="digg"], [class*="count"]');
                            likeElements.forEach(likeEl => {
                                const likeText = likeEl.textContent || '';
                                const match = likeText.match(/\\d+/);
                                if (match) likes = Math.max(likes, parseInt(match[0]));
                            });

                            // Try to extract user info
                            let username = 'unknown';
                            const userElements = commentContainer.querySelectorAll('[class*="user"], [class*="name"], [class*="author"]');
                            userElements.forEach(userEl => {
                                const userText = userEl.textContent?.trim();
                                if (userText && userText.length > 0 && userText.length < 50) {
                                    username = userText;
                                }
                            });

                            results.push({
                                text: text,
                                likes: likes,
                                username: username,
                                html: commentContainer.outerHTML.substring(0, 500)
                            });
                        }
                    }
                }

                return results;
            }""")

            # Process results and deduplicate
            for comment_data in all_text_content:
                text = comment_data.get("text", "").strip()

                if not text or len(text) < 2:
                    continue

                # Create hash to avoid duplicates
                text_hash = hash(text)

                if text_hash in self.seen_hashes:
                    continue

                self.seen_hashes.add(text_hash)

                new_comments.append({
                    "text": text,
                    "likes": comment_data.get("likes", 0),
                    "username": comment_data.get("username", "anonymous"),
                    "timestamp": datetime.now().isoformat(),
                })

        except Exception as e:
            print(f"⚠️  提取评论失败: {e}")

        return new_comments

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from Douyin URL."""
        try:
            if "modal_id=" in url:
                return url.split("modal_id=")[-1].split("&")[0]
            elif "/video/" in url:
                return url.split("/video/")[-1].split("?")[0]
            else:
                return "unknown"
        except:
            return "unknown"

    def _print_summary(self, result: dict, output_file: Path):
        """Print summary of scraping results."""
        print("\n" + "=" * 70)
        print("📊 爬取结果摘要")
        print("=" * 70)

        print(f"\n✅ 状态: {'成功' if result['success'] else '失败'}")
        print(f"📝 评论数量: {result['total_comments']}")
        print(f"🎥 视频 ID: {result['video_id']}")

        if result['comments']:
            total_likes = sum(c.get('likes', 0) for c in result['comments'])
            avg_likes = total_likes / len(result['comments']) if result['comments'] else 0

            print(f"👍 总点赞数: {total_likes}")
            print(f"📈 平均点赞: {avg_likes:.1f}")

            # Show top 5 comments by likes
            top_comments = sorted(
                result['comments'], key=lambda x: x.get('likes', 0), reverse=True
            )[:5]

            print(f"\n💬 热门评论 (Top 5):")
            for i, comment in enumerate(top_comments, 1):
                print(f"   {i}. [{comment.get('likes', 0)} 赞] {comment.get('text', '')[:80]}")
                if comment.get('username'):
                    print(f"      👤 {comment.get('username', 'anonymous')}")

        print(f"\n💾 结果已保存到: {output_file}")
        print("=" * 70)

        if result['total_comments'] == 0:
            print("\n⚠️  未获取到评论，可能原因:")
            print("   1. 需要登录才能查看评论")
            print("   2. 视频已删除或不存在")
            print("   3. 反爬虫检测，建议:")
            print("      - 等待更长时间后重试")
            print("      - 使用代理IP")
            print("      - 降低滚动速度")
            print("   4. 页面结构已变化，需要更新选择器")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("用法: python3 douyin_pro.py <抖音视频URL> [选项]")
        print("\n选项:")
        print("  --headless     无头模式运行（默认：显示浏览器窗口）")
        print("  --max N        最多爬取N条评论")
        print("  --proxy URL     使用代理")
        print("\n示例:")
        print("python3 douyin_pro.py 'https://www.douyin.com/user/...?modal_id=7597795827700487787'")
        print("python3 douyin_pro.py '<URL>' --max 50 --headless")
        return

    url = sys.argv[1]

    # Parse options
    headless = "--headless" in sys.argv
    max_comments = None

    for i, arg in enumerate(sys.argv):
        if arg == "--max" and i + 1 < len(sys.argv):
            try:
                max_comments = int(sys.argv[i + 1])
            except ValueError:
                pass

    # Create scraper
    scraper = DouyinScraperPro(headless=headless)

    # Run scraping
    try:
        result = await scraper.scrape(url, max_comments=max_comments)

        if result['success']:
            print("\n✅ 爬取成功完成！")
            return 0
        else:
            print("\n❌ 未能获取到评论")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
