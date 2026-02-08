# TikTok/Douyin Comment Scraper with AI Analysis

一个功能强大的TikTok/抖音评论爬虫，集成大语言模型进行情感分析和摘要生成。

## 特性

- 🔍 **智能爬虫**: 支持Playwright浏览器自动化和隐藏API两种爬取方式
- 🛡️ **反爬机制**: 用户代理轮换、请求延迟、Webdriver隐藏、代理支持
- 🤖 **AI分析**: 使用GLM-4.7进行情感分析和评论摘要
- 📊 **情感分类**: 自动识别积极、消极、中立、建议和疑问评论
- 📝 **智能摘要**: 生成全面的评论总结和关键点提取
- 🧪 **测试驱动**: 完整的单元测试覆盖，TDD开发模式
- 🔄 **失败重试**: 指数退避重试机制
- 📦 **批处理**: 高效的批量处理和并发控制

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/HalFTeen/commit-summary.git
cd commit-summary

# 安装依赖 (推荐使用Poetry)
pip install poetry
poetry install

# 或使用pip
pip install -r requirements.txt
```

### 配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑`.env`文件，设置Z.ai API密钥：
```env
ZAI_API_KEY=your_zai_api_key_here
ZAI_MODEL=glm-4.7
ZAI_TIMEOUT=300
ZAI_MAX_RETRIES=3

ENABLE_FALLBACK=true

TIKTOK_TIMEOUT=30
TIKTOK_MAX_RETRIES=5
TIKTOK_REQUEST_DELAY=1.0

OUTPUT_DIR=output
BATCH_SIZE=50
```

### 安装Playwright浏览器

```bash
playwright install chromium
```

## 使用方法

### 命令行使用

```bash
# 基本使用
python -m tiktok_comment_scraper.cli <TikTok视频URL>

# 限制评论数量
python -m tiktok_comment_scraper.cli <URL> --max-comments 100

# 使用浏览器模式（更可靠但较慢）
python -m tiktok_comment_scraper.cli <URL> --use-browser

# 自定义输出目录
python -m tiktok_comment_scraper.cli <URL> --output-dir ./results

# 指定API密钥
python -m tiktok_comment_scraper.cli <URL> --api-key your_api_key

# 自定义模型和批处理大小
python -m tiktok_comment_scraper.cli <URL> --model glm-4.7 --batch-size 20
```

### Python代码使用

```python
import asyncio
from tiktok_comment_scraper.scraper.tiktok import TikTokAPIScraper
from tiktok_comment_scraper.llm.client import LLMClient
from tiktok_comment_scraper.models.comment import VideoSummary

async def main():
    # 爬取评论
    scraper = TikTokAPIScraper()
    comments = await scraper.scrape_video_comments(
        "https://www.tiktok.com/@user/video/1234567890",
        max_comments=100
    )

    print(f"爬取到 {len(comments)} 条评论")

    # 分析评论
    llm_client = LLMClient()
    analysis_results = llm_client.batch_analyze(comments)

    # 生成摘要
    summary = llm_client.summarize_comments(comments)

    print(f"摘要: {summary}")

    # 创建视频摘要
    video_summary = VideoSummary(
        video_id="1234567890",
        total_comments=len(comments),
        comments=comments,
        analysis_results=analysis_results,
        overall_summary=summary
    )

    video_summary.calculate_sentiment_distribution()
    print(f"情感分布: {video_summary.sentiment_distribution}")

asyncio.run(main())
```

## 项目结构

```
commit-summary/
├── src/
│   └── tiktok_comment_scraper/
│       ├── config/           # 配置管理
│       │   └── settings.py
│       ├── scraper/          # 爬虫实现
│       │   └── tiktok.py
│       ├── llm/             # LLM集成
│       │   └── client.py
│       ├── models/          # 数据模型
│       │   └── comment.py
│       └── cli.py           # 命令行接口
├── tests/                  # 测试
│   ├── unit/
│   └── integration/
├── config/                 # 配置文件
├── output/                 # 输出目录
├── pyproject.toml         # 项目配置
├── .env.example          # 环境变量模板
└── README.md
```

## 数据模型

### Comment (评论)
- `comment_id`: 评论唯一标识
- `video_id`: 视频ID
- `text`: 评论内容
- `author`: 作者信息 (用户名、头像等)
- `like_count`: 点赞数
- `reply_count`: 回复数
- `parent_comment_id`: 父评论ID (用于回复)
- `created_at`: 创建时间
- `is_pinned`: 是否置顶
- `sentiment`: 情感分类

### Sentiment (情感类型)
- `POSITIVE`: 积极
- `NEGATIVE`: 消极
- `NEUTRAL`: 中立
- `SUGGESTION`: 建议
- `QUESTION`: 疑问

### AnalysisResult (分析结果)
- `comment_id`: 评论ID
- `sentiment`: 情感分类
- `confidence`: 置信度 (0.0-1.0)
- `key_points`: 关键点列表
- `summary`: 简要摘要

## 测试

运行所有测试：
```bash
# 使用pytest
pytest

# 带覆盖率报告
pytest --cov=src/tiktok_comment_scraper --cov-report=html

# 只运行单元测试
pytest tests/unit -m unit

# 只运行集成测试
pytest tests/integration -m integration
```

## 反爬虫机制

项目实现了多层反爬虫保护：

1. **用户代理轮换**: 使用fake-useragent随机生成UA
2. **请求延迟**: 随机延迟避免高频请求
3. **Webdriver隐藏**: 注入脚本隐藏自动化特征
4. **代理支持**: 支持HTTP/HTTPS代理
5. **重试机制**: 指数退避重试失败请求
6. **Cookie管理**: 浏览器上下文保持会话

## LLM配置

### Z.ai GLM-4.7

默认使用Z.ai的GLM-4.7模型进行情感分析和摘要生成。

**获取API密钥**:
1. 访问 [Z.ai开放平台](https://z.ai/model-api)
2. 注册/登录账号
3. 在[API密钥管理](https://z.ai/manage-apikey/apikey-list)创建密钥
4. 将密钥配置到`.env`文件

**模型能力**:
- 200K上下文窗口
- 支持结构化输出 (JSON)
- 中文优化
- 高准确率情感分析

### 失败回退

当主API失败时，系统会自动重试。可以通过配置启用/禁用回退机制。

## 输出格式

爬取和分析的结果会保存为JSON文件：

```json
{
  "video_id": "1234567890",
  "total_comments": 100,
  "comments": [...],
  "analysis_results": [
    {
      "comment_id": "c1",
      "sentiment": "positive",
      "confidence": 0.95,
      "key_points": ["内容精彩", "学到很多"],
      "summary": "用户对视频非常满意"
    }
  ],
  "overall_summary": "这条视频获得了大量正面反馈...",
  "sentiment_distribution": {
    "positive": 70,
    "neutral": 20,
    "negative": 5,
    "suggestion": 3,
    "question": 2
  }
}
```

## 注意事项

1. **遵守平台条款**: 使用本工具需遵守TikTok/抖音的服务条款
2. **合理使用**: 避免高频请求，设置适当延迟
3. **API限额**: 注意Z.ai API的调用限额和费用
4. **隐私保护**: 不要爬取和存储用户敏感信息
5. **仅供学习**: 本工具仅供学习和研究使用

## 常见问题

### Q: 爬虫无法获取评论怎么办？

A: 尝试以下方法：
- 使用`--use-browser`参数切换到浏览器模式
- 检查网络连接和代理设置
- 增加请求延迟时间
- 确认视频URL是否正确

### Q: LLM分析失败怎么办？

A: 检查：
- API密钥是否正确配置
- 网络是否能访问Z.ai API
- API额度是否充足
- 检查错误日志获取详细信息

### Q: 如何提高爬取速度？

A: 可以：
- 使用API模式而非浏览器模式
- 增加`BATCH_SIZE`参数
- 减少`TIKTOK_REQUEST_DELAY` (但可能导致封禁)
- 限制`max_comments`数量

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 致谢

- [Playwright](https://playwright.dev/) - 浏览器自动化
- [Z.ai](https://z.ai/) - GLM-4.7模型支持
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证
- [pytest](https://docs.pytest.org/) - 测试框架
