# 环境设置指南

## 测试结果 ✅

测试抖音URL成功：
- ✓ URL解析成功
- ✓ 视频ID提取: `7597795827700487787`
- ✓ 用户ID提取: `MS4wLjABAAAAP4BoVo5c_VqnejG2sPEmZJPL3wOm7sIaa2ZmIKH2D9A`
- ✓ 测试结果已保存到 `output/test_results.json`

## 已安装依赖

- ✅ python 3.9.6
- ✅ pip 26.0.1
- ✅ httpx (HTTP客户端)
- ✅ pydantic (数据验证)
- ❌ playwright (浏览器自动化) - 安装中...
- ❌ zai-sdk (LLM集成) - 需要安装

## 手动安装步骤

由于网络原因，部分依赖安装超时。请手动执行以下命令：

### 1. 安装Playwright

```bash
# 安装playwright包
python3 -m pip install playwright

# 安装Chromium浏览器
python3 -m playwright install chromium
```

如果下载太慢，可以使用国内镜像：

```bash
# 设置环境变量使用镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net

# 然后安装
python3 -m pip install playwright
python3 -m playwright install chromium
```

### 2. 安装Z.ai SDK

```bash
python3 -m pip install zai-sdk
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的Z.ai API密钥：

```env
ZAI_API_KEY=your_actual_api_key_here
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

### 4. 获取Z.ai API密钥

1. 访问: https://z.ai/model-api
2. 注册/登录账号
3. 创建API密钥: https://z.ai/manage-apikey/apikey-list
4. 复制密钥到 `.env` 文件

## 测试命令

### 运行测试脚本

```bash
python3 test_scraper.py "https://www.douyin.com/user/MS4wLjABAAAAP4BoVo5c_VqnejG2sPEmZJPL3wOm7sIaa2ZmIKH2D9A?from_tab_name=main&modal_id=7597795827700487787"
```

### 运行完整爬虫 (依赖安装后)

```bash
# 使用API模式 (快速)
python3 -m tiktok_comment_scraper.cli "https://www.douyin.com/user/MS4wLjABAAAAP4BoVo5c_VqnejG2sPEmZJPL3wOm7sIaa2ZmIKH2D9A?from_tab_name=main&modal_id=7597795827700487787"

# 使用浏览器模式 (可靠但慢)
python3 -m tiktok_comment_scraper.cli "https://www.douyin.com/user/MS4wLjABAAAAP4BoVo5c_VqnejG2sPEmZJPL3wOm7sIaa2ZmIKH2D9A?from_tab_name=main&modal_id=7597795827700487787" --use-browser

# 限制评论数量
python3 -m tiktok_comment_scraper.cli "<URL>" --max-comments 20
```

## 故障排除

### Playwright安装失败

如果Playwright安装失败，尝试：

```bash
# 使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 或者手动下载
python3 -m playwright install --with-deps chromium
```

### 网络问题

如果下载速度慢，使用国内镜像源：

```bash
# 临时使用清华镜像
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple playwright zai-sdk
```

### Z.ai API连接问题

检查：
1. 网络是否能访问 `https://api.z.ai`
2. API密钥是否正确
3. 账户是否有余额

## 项目文件说明

- `test_scraper.py` - 简单测试脚本，无需完整依赖
- `src/tiktok_comment_scraper/cli.py` - 完整CLI工具
- `src/tiktok_comment_scraper/scraper/tiktok.py` - TikTok/抖音爬虫
- `src/tiktok_comment_scraper/llm/client.py` - LLM客户端
- `output/test_results.json` - 测试结果

## 下一步

1. 完成依赖安装
2. 配置API密钥
3. 运行完整爬虫测试
4. 查看结果JSON文件
