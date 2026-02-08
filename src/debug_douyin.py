"""Debug script to inspect Douyin page structure."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fake_useragent import UserAgent
from playwright.async_api import async_playwright


async def debug_page(url: str):
    """Debug and inspect the page structure."""
    print("🔍 调试抖音页面...")
    print(f"📍 URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=UserAgent().random,
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )

        page = await context.new_page()

        print("📄 加载页面...")
        await page.goto(url, timeout=60000, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # 1. Get page title
        title = await page.title()
        print(f"\n📋 页面标题: {title}")

        # 2. Get page URL
        current_url = page.url
        print(f"🔗 当前URL: {current_url}")

        # 3. Check for login requirement
        login_check = await page.evaluate("""() => {
            const loginIndicators = [
                document.body.innerText.includes('登录'),
                document.body.innerText.includes('Login'),
                document.querySelector('[class*="login"]'),
                document.querySelector('#login'),
                document.querySelector('.login-btn'),
            ];
            return {
                hasLogin: loginIndicators.some(x => x === true),
                bodyTextLength: document.body.innerText.length,
                bodyHTMLLength: document.body.innerHTML.length
            };
        }""")

        print(f"\n🔐 登录检查:")
        print(f"   - 需要登录: {'是' if login_check['hasLogin'] else '否'}")
        print(f"   - 页面文本长度: {login_check['bodyTextLength']}")
        print(f"   - 页面HTML长度: {login_check['bodyHTMLLength']}")

        # 4. Search for comment-related keywords
        comment_check = await page.evaluate("""() => {
            const bodyText = document.body.innerText.toLowerCase();
            const keywords = [
                '评论', 'comment', '说点什么', '留言',
                '回复', 'reply', '点赞', '喜欢'
            ];
            return keywords.map(kw => ({
                keyword: kw,
                found: bodyText.includes(kw)
            }));
        }""")

        print(f"\n💬 评论关键词检查:")
        found_keywords = [ck for ck in comment_check if ck['found']]
        for ck in found_keywords[:10]:
            print(f"   - 找到: {ck['keyword']}")

        if not found_keywords:
            print("   - 未找到评论相关关键词")

        # 5. Try to find any text blocks
        text_blocks = await page.evaluate("""() => {
            const allElements = document.querySelectorAll('*');
            const textBlocks = [];

            for (let el of allElements) {
                const text = el.textContent?.trim();
                if (text && text.length > 5 && text.length < 200) {
                    // Check if it might be user-generated content
                    const parent = el.parentElement;
                    const hasInteraction = parent && (
                        parent.querySelector('[class*="like"]') ||
                        parent.querySelector('[class*="reply"]') ||
                        parent.querySelector('[class*="digg"]') ||
                        parent.querySelector('button')
                    );

                    if (hasInteraction) {
                        textBlocks.push({
                            text: text.substring(0, 100),
                            tag: el.tagName,
                            class: el.className?.substring(0, 50)
                        });
                    }
                }
            }

            return textBlocks.slice(0, 20);
        }""")

        print(f"\n📝 潜在文本块 (前20):")
        for i, block in enumerate(text_blocks[:10], 1):
            print(f"   {i}. <{block['tag']}> {block['text'][:60]}...")
            if block['class']:
                print(f"      class: {block['class'][:40]}")

        # 6. Get all div classes
        all_classes = await page.evaluate("""() => {
            const classes = new Set();
            document.querySelectorAll('div').forEach(div => {
                if (div.className) {
                    div.className.split(/\\s+/).forEach(cls => classes.add(cls));
                }
            });
            return Array.from(classes).filter(cls => 
                cls.toLowerCase().includes('comment') || 
                cls.toLowerCase().includes('reply') ||
                cls.toLowerCase().includes('list') ||
                cls.toLowerCase().includes('item')
            ).slice(0, 30);
        }""")

        print(f"\n🏷️  包含关键词的CSS类:")
        for cls in all_classes[:15]:
            print(f"   - {cls}")

        # 7. Take a screenshot
        screenshot_path = Path("output") / "debug_screenshot.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 截图已保存: {screenshot_path}")

        # 8. Save page HTML
        html_path = Path("output") / "debug_page.html"
        with open(html_path, "w", encoding="utf-8") as f:
            html_content = await page.content()
            f.write(html_content)
        print(f"📄 页面HTML已保存: {html_path}")

        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 debug_douyin.py <抖音URL>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        asyncio.run(debug_page(url))
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
