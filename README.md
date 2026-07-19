# 🌍 AI-Powered Financial News & Research Bot
**AI 智能金融情报推送机器人 (DeepSeek + DingTalk)**

[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-green.svg)](https://platform.deepseek.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English Version Below](#english-version)

---

## 🇨🇳 中文说明 (Chinese Version)

### 📌 项目简介
这是一个轻量级、完全免费（依托 GitHub Actions）的自动化金融情报系统。它能够每天定时抓取顶级财经媒体（如 Financial Times、Forbes）以及谷歌学术的最新动态，利用 **DeepSeek AI** 进行深度阅读、过滤和提炼，最终生成结构化的中文简报，直接推送到你的**钉钉 (DingTalk)** 手机端。

**默认关注领域**：商品、期货、原油、黄金、财务舞弊、内部控制。

### 🚀 快速部署指南（保姆级）

无需购买服务器，无需本地安装环境，只需按以下步骤操作，即可在 5 分钟内拥有属于你自己的 AI 简报机器人：

#### 1. 准备工作 (获取两个关键密钥)
* **钉钉机器人 Webhook**：在钉钉建一个单人群，点击群设置 -> 智能群助手 -> 添加机器人 -> 选择“自定义” -> 安全设置勾选“自定义关键词”并填入 `新闻` -> 复制 Webhook 链接。
* **DeepSeek API Key**：前往 [DeepSeek 开放平台](https://platform.deepseek.com/) 注册账号，在 API Keys 菜单中生成一个以 `sk-` 开头的密钥。

#### 2. 复制 (Fork) 本项目
* 点击页面右上角的 **`Fork`** 按钮，将这个项目复制到你自己的 GitHub 账号下。

#### 3. 配置环境变量 (Secrets)
为了安全，绝对不要把密钥写在代码里！请将密钥配置在 GitHub 仓库设置中：
1.  进入你 Fork 后的仓库，点击顶部 **`Settings`**。
2.  在左侧菜单依次展开 **`Secrets and variables`** -> **`Actions`**。
3.  点击 **`New repository secret`**，添加以下两个变量：
    * Name 填 `DINGTALK_WEBHOOK`，Value 填 你的钉钉链接。
    * Name 填 `DEEPSEEK_API_KEY`，Value 填 你的 DeepSeek 密钥。

#### 4. 启用并测试自动化运行
1.  点击仓库顶部的 **`Actions`** 选项卡。
2.  点击绿色的 **`I understand my workflows, go ahead and enable them`** 按钮开启自动化。
3.  在左侧点击 **`News Push Bot`**，然后点击右侧的 **`Run workflow`** 手动运行一次。
4.  等待约 1 分钟，你的手机钉钉就会收到第一份 AI 简报！(默认每天北京时间早上 8:00 自动运行)。

---

### 🛠️ 高级：如何自定义新闻来源和关键词？

如果你想监控其他的网站或其他的行业关键词，只需修改仓库中的 **`main.py`** 文件。

#### 1. 修改新闻来源 (RSS)
在 `main.py` 的第 15 行左右，找到 `NEWS_SOURCES` 字典。你可以添加任何支持 RSS 的新闻网站链接：
```python
NEWS_SOURCES = {
    "Financial Times (金融时报)": "[https://www.ft.com/markets?format=rss](https://www.ft.com/markets?format=rss)",
    "Forbes (福布斯市场)": "[https://www.forbes.com/markets/feed/](https://www.forbes.com/markets/feed/)",
    "WSJ (华尔街日报)": "你的新RSS链接" # 👈 在这里添加新的来源
}
