"""Douyin API-based comment scraper."""

import asyncio
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import httpx
from fake_useragent import UserAgent


class DouyinAPIScraper:
    """Douyin comment scraper using internal API."""

    def __init__(self):
        """Initialize API scraper."""
        self.base_url = "https://www.douyin.com"
        self.api_url = "https://www.douyin.com/aweme/v1/web/comment/list/"
        self.timeout = 30
        self.user_agent = UserAgent().random
        self.cookies = {}  # Will be populated from page load

    async def scrape(self, video_url: str, max_comments: Optional[int] = None) -> dict:
        """Scrape comments using API approach.

        Args:
            video_url: Douyin video URL
            max_comments: Maximum comments to scrape

        Returns:
            Dictionary with results
        """
        print("=" * 70)
        print("🔍 抖音API评论爬虫")
        print("=" * 70)
        print(f"\n📍 目标URL: {video_url}")

        # Extract video ID
        video_id = self._extract_video_id(video_url)
        if not video_id:
            print("❌ 无法提取视频ID")
            return {"success": False, "error": "Invalid URL"}

        print(f"🎥 视频 ID: {video_id}")

        comments = []
        cursor = "0"
        page_count = 0
        max_pages = 50

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, try to get initial cookies
                print("\n🔄 获取初始cookies...")
                await self._get_initial_cookies(client, video_url)

                # Fetch comments with pagination
                print("🔄 开始获取评论...\n")

                while page_count < max_pages:
                    if max_comments and len(comments) >= max_comments:
                        print(f"✅ 已达到目标评论数: {max_comments}")
                        break

                    # Build API request
                    params = {
                        "aweme_id": video_id,
                        "count": "20",
                        "cursor": cursor,
                    }

                    headers = {
                        "User-Agent": self.user_agent,
                        "Referer": f"{self.base_url}/",
                        "Cookie": self._format_cookies(),
                    }

                    print(f"📥 获取第 {page_count + 1} 页... (cursor: {cursor})")

                    try:
                        response = await client.get(
                            self.api_url, params=params, headers=headers
                        )

                        print(f"   状态码: {response.status_code}")
                        print(f"   响应长度: {len(response.content)} 字节")

                        if response.status_code != 200:
                            print(f"   ⚠️  HTTP错误: {response.status_code}")
                            print(f"   响应: {response.text[:200]}")

                            # Try alternative approach
                            if page_count == 0:
                                print("\n🔄 尝试备用API端点...")
                                alt_result = await self._try_alternative_api(
                                    client, video_id, max_comments
                                )
                                if alt_result["success"]:
                                    return alt_result

                            break

                        data = response.json()

                        # Check response structure
                        if not data.get("aweme_comments"):
                            print("   ⚠️  无评论数据")
                            print(f"   响应结构: {list(data.keys())}")
                            break

                        comments_list = data.get("aweme_comments", [])

                        if not comments_list:
                            print("   ℹ️  已无更多评论")
                            break

                        # Process comments
                        new_comments = self._parse_comments(comments_list, video_id)
                        comments.extend(new_comments)

                        print(f"   ✅ 获取 {len(new_comments)} 条 (总计: {len(comments)})")

                        # Get next cursor
                        cursor = data.get("cursor", "")
                        if not cursor:
                            print("   ℹ️  无更多页")
                            break

                        page_count += 1

                        # Rate limiting delay
                        delay = random.uniform(0.5, 1.5)
                        await asyncio.sleep(delay)

                    except httpx.TimeoutException:
                        print("   ⚠️  请求超时")
                        break
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  JSON解析错误: {e}")
                        print(f"   响应内容: {response.text[:200]}")
                        break
                    except Exception as e:
                        print(f"   ⚠️  错误: {e}")
                        break

        except Exception as e:
            print(f"\n❌ 爬取失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        # Prepare result
        result = {
            "video_url": video_url,
            "video_id": video_id,
            "total_comments": len(comments),
            "comments": comments,
            "pages_loaded": page_count,
            "scraped_at": datetime.now().isoformat(),
            "scraper_version": "2.0.0",
            "success": len(comments) > 0,
        }

        # Save results
        output_file = Path("output") / f"douyin_api_{video_id}_{int(time.time())}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self._print_summary(result, output_file)

        return result

    async def _get_initial_cookies(self, client: httpx.AsyncClient, url: str):
        """Get initial cookies from the video page."""
        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
            }

            response = await client.get(url, headers=headers, follow_redirects=True)

            # Extract cookies - handle both CookieJar and list
            if hasattr(response.cookies, 'items'):
                for name, value in response.cookies.items():
                    self.cookies[name] = value
            else:
                for cookie in response.cookies:
                    self.cookies[cookie.name] = cookie.value if hasattr(cookie, 'value') else cookie

            print(f"✅ 获取到 {len(self.cookies)} 个cookies")

        except Exception as e:
            print(f"⚠️  获取cookies失败: {e}")

    def _format_cookies(self) -> str:
        """Format cookies for HTTP header."""
        return "; ".join([f"{k}={v}" for k, v in self.cookies.items()])

    async def _try_alternative_api(
        self, client: httpx.AsyncClient, video_id: str, max_comments: Optional[int]
    ) -> dict:
        """Try alternative API endpoints."""
        print("\n🔄 尝试备用API方法...")

        alternative_urls = [
            "https://www.douyin.com/aweme/v1/web/comment/list/",
            "https://www.douyin.com/comment/v2/list/",
        ]

        comments = []

        for api_url in alternative_urls:
            try:
                print(f"   🔍 尝试: {api_url.split('/')[-3]}")

                params = {"aweme_id": video_id, "count": "20", "cursor": "0"}

                headers = {
                    "User-Agent": self.user_agent,
                    "Referer": self.base_url,
                    "Cookie": self._format_cookies(),
                }

                response = await client.get(api_url, params=params, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    # Try different response structures
                    if "comments" in data:
                        comments_list = data["comments"]
                    elif "aweme_comments" in data:
                        comments_list = data["aweme_comments"]
                    elif "data" in data and "comments" in data["data"]:
                        comments_list = data["data"]["comments"]
                    else:
                        continue

                    if comments_list:
                        parsed = self._parse_comments(comments_list, video_id)
                        comments.extend(parsed)
                        print(f"   ✅ 备用API成功! 获取 {len(parsed)} 条")
                        break

            except Exception as e:
                print(f"   ❌ 失败: {e}")
                continue

        if comments:
            return {
                "video_id": video_id,
                "total_comments": len(comments),
                "comments": comments,
                "scraped_at": datetime.now().isoformat(),
                "success": True,
            }

        return {"success": False, "error": "All API attempts failed"}

    def _parse_comments(self, comments_list: List[dict], video_id: str) -> List[dict]:
        """Parse comment data from API response."""
        parsed = []

        for idx, comment_data in enumerate(comments_list):
            try:
                # Try different field names
                text = (
                    comment_data.get("text")
                    or comment_data.get("comment_text")
                    or ""
                )

                if not text:
                    continue

                # Parse user info
                user_data = comment_data.get("user", {})
                username = (
                    user_data.get("nickname")
                    or user_data.get("unique_id")
                    or user_data.get("uid", "")
                )

                # Parse likes
                likes = comment_data.get("digg_count", comment_data.get("like_count", 0))

                parsed.append(
                    {
                        "comment_id": comment_data.get("cid", f"{video_id}_{idx}"),
                        "video_id": video_id,
                        "text": text,
                        "username": username,
                        "likes": likes,
                        "timestamp": datetime.now().isoformat(),
                        "user_id": str(
                            user_data.get("uid", user_data.get("id", ""))
                        ),
                    }
                )
            except Exception as e:
                print(f"   ⚠️  解析评论错误: {e}")
                continue

        return parsed

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        try:
            if "modal_id=" in url:
                return url.split("modal_id=")[-1].split("&")[0]
            elif "/video/" in url:
                return url.split("/video/")[-1].split("?")[0]
            else:
                return ""
        except:
            return ""

    def _print_summary(self, result: dict, output_file: Path):
        """Print scraping summary."""
        print("\n" + "=" * 70)
        print("📊 API爬取结果")
        print("=" * 70)

        print(f"\n✅ 状态: {'成功' if result['success'] else '失败'}")
        print(f"📝 评论数量: {result['total_comments']}")

        if "pages_loaded" in result:
            print(f"📄 加载页数: {result['pages_loaded']}")

        if result["comments"]:
            total_likes = sum(c.get("likes", 0) for c in result["comments"])
            avg_likes = (
                total_likes / len(result["comments"]) if result["comments"] else 0
            )

            print(f"👍 总点赞数: {total_likes}")
            print(f"📈 平均点赞: {avg_likes:.1f}")

            print(f"\n💬 前10条评论:")
            for i, comment in enumerate(result["comments"][:10], 1):
                print(f"   {i}. [{comment.get('likes', 0)} 赞] {comment.get('text', '')[:80]}")
                if comment.get("username"):
                    print(f"      👤 {comment.get('username', 'unknown')}")

        print(f"\n💾 结果已保存: {output_file}")
        print("=" * 70)


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("用法: python3 douyin_api.py <抖音视频URL> [选项]")
        print("\n选项:")
        print("  --max N        最多爬取N条评论")
        print("\n示例:")
        print("python3 douyin_api.py 'https://www.douyin.com/user/...?modal_id=7597795827700487787'")
        print("python3 douyin_api.py '<URL>' --max 100")
        return

    url = sys.argv[1]

    max_comments = None
    for i, arg in enumerate(sys.argv):
        if arg == "--max" and i + 1 < len(sys.argv):
            try:
                max_comments = int(sys.argv[i + 1])
            except ValueError:
                pass

    scraper = DouyinAPIScraper()

    try:
        result = await scraper.scrape(url, max_comments=max_comments)

        if result["success"]:
            print("\n✅ 爬取成功!")
            return 0
        else:
            print("\n❌ 爬取失败")
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
