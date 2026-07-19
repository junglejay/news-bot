import feedparser
import requests
import json
import os
from openai import OpenAI

# 获取环境变量
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK")

# AI 服务配置：中转服务（OpenAI 兼容）。密钥通过环境变量 AI_API_KEY 注入，勿硬编码进代码。
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://minitoken.top/v1")
AI_MODEL = os.environ.get("AI_MODEL", "deepseek-v4-flash")

if not AI_API_KEY:
    raise SystemExit("❌ 未检测到 AI_API_KEY，请在本地设置环境变量，或在 GitHub 仓库 Secrets 中配置 AI_API_KEY。")

# 快速调试模式：QUICK_MODE=1 启用，只抓少量内容以节省时间和 API 额度
QUICK_MODE = os.environ.get("QUICK_MODE", "").lower() in ("1", "true", "yes")
if QUICK_MODE:
    MAX_SOURCES = 1          # 最多抓取的新闻源数量
    SCAN_ENTRIES = 5         # 每个源扫描的条目数
    MAX_PER_SOURCE = 1       # 每个源精选的条目数
    ENABLE_SCHOLAR = False   # 是否抓取学术模块
else:
    MAX_SOURCES = None       # None 表示不限制
    SCAN_ENTRIES = 20
    MAX_PER_SOURCE = 3
    ENABLE_SCHOLAR = True

# 初始化 AI 客户端
client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

# 扩展后的新闻源：涵盖外媒、大宗商品专业频道、全球经济动态
NEWS_SOURCES = {
    "Financial Times (金融时报)": "https://www.ft.com/markets?format=rss",
    "Forbes (福布斯市场)": "https://www.forbes.com/markets/feed/",
    "BBC Business (BBC商业)": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "The Guardian Business (卫报商业)": "https://www.theguardian.com/business/rss"
}

# 扩展后的核心监控关键词
TARGET_KEYWORDS = [
    # 原有：期货/大宗/内控
    "期货", "商品", "大宗", "原油", "黄金", "铜", "commodity", "futures",
    "财务舞弊", "内部控制", "审计", "fraud", "internal control", "audit",
    # 新增：四大事务所 (Big Four)
    "德勤", "普华永道", "毕马威", "安永", "Deloitte", "PwC", "KPMG", "EY", "Big Four",
    # 新增：全球大宗商品交易
    "贸易商", "Trafigura", "Glencore", "Vitol", "仓单", "inventory", "supply chain",
    # 新增：汇率及利率
    "汇率", "利率", "美联储", "加息", "降息", "央行", "人民币", "美元指数", 
    "exchange rate", "interest rate", "Fed", "central bank", "USD", "CNY"
]

def is_target_news(text):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in TARGET_KEYWORDS)

def get_full_text(url):
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=20)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"网页抓取失败 ({url}): {e}")
    return ""

def ai_summarize_news(full_text):
    if not full_text or len(full_text) < 100:
        return "网页内容过短或抓取受限，无法进行 AI 深度总结。"
        
    content = full_text[:8000] 
    prompt = f"""
    你是一个专业的金融与风控分析师。请阅读以下新闻正文，输出中文总结。
    需特别关注：四大行调研、全球大宗商品供需、汇率/利率变动趋势。
    
    格式要求：
    **🎯 核心结论**：（一句话概括核心影响）
    **📝 详细提炼**：
    - （事实、数据、政策变动等要点）
    
    新闻正文：
    {content}
    """
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return "AI 新闻总结出错。"

def fetch_scholar_research():
    """多引擎抓取：学术 + 四大事务所报告"""
    tasks = {
        "📊 模块A：商品与期货市场": "https://scholar.google.com/scholar?q=%E5%95%86%E5%93%81+%E6%9C%9F%E8%B4%A7&scisbd=1",
        "🚨 模块B：财务舞弊与内控": "https://scholar.google.com/scholar?q=%E8%B4%A2%E5%8A%A1%E8%88%9E%E5%BC%8A+%E5%86%85%E9%83%A8%E6%8E%A7%E5%88%B6&scisbd=1",
        "🏛️ 模块C：四大事务所研究报告 (Big 4)": "https://www.google.com/search?q=Deloitte+PwC+EY+KPMG+research+report+2024+2025"
    }
    
    academic_report = ""
    for topic, url in tasks.items():
        try:
            print(f"正在获取: {topic}")
            jina_url = f"https://r.jina.ai/{url}"
            response = requests.get(jina_url, timeout=20)
            if response.status_code == 200:
                content = response.text[:6000]
                prompt = f"你是一个专业研究助手。请从以下抓取内容中提炼关于【{topic}】的最新的真实研究标题和核心观点。若内容被拦截，请回复\"抓取受限\"。\n\n内容：{content}"
                res = client.chat.completions.create(
                    model=AI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                academic_report += f"#### {topic}\n> {res.choices[0].message.content}\n\n"
        except Exception as e:
            print(f"⚠️ 模块获取失败 ({topic}): {e}")
            continue
    return academic_report + "---\n"

def send_dingtalk(text):
    # 本地调试模式：未配置 DINGTALK_WEBHOOK 时直接打印，不推送
    if not DINGTALK_WEBHOOK:
        print("\n" + "=" * 60)
        print("【本地调试模式】未检测到 DINGTALK_WEBHOOK，直接打印简报内容：")
        print("=" * 60)
        print(text)
        return
    headers = {'Content-Type': 'application/json'}
    data = {"msgtype": "markdown", "markdown": {"title": "专业领域简报", "text": text}}
    requests.post(DINGTALK_WEBHOOK, data=json.dumps(data), headers=headers)

def fetch_news():
    final_message = "### 🌍 综合领域情报与深度简报\n\n"
    if ENABLE_SCHOLAR:
        final_message += fetch_scholar_research()

    sources = list(NEWS_SOURCES.items())
    if MAX_SOURCES is not None:
        sources = sources[:MAX_SOURCES]

    for name, rss_url in sources:
        feed = feedparser.parse(rss_url)
        source_message = f"#### 📢 {name}\n"
        count = 0
        for entry in feed.entries[:SCAN_ENTRIES]:
            if count >= MAX_PER_SOURCE: break  # 每个源最多选 N 条精华
            if is_target_news(entry.title + " " + getattr(entry, 'summary', '')):
                full_article = get_full_text(entry.link)
                ai_report = ai_summarize_news(full_article)
                source_message += f"**原文**: [{entry.title}]({entry.link})\n> {ai_report}\n\n"
                count += 1
        final_message += source_message

    send_dingtalk(final_message)
    print("推送完毕！")

if __name__ == "__main__":
    if QUICK_MODE:
        print("=" * 60)
        print("⚡ 快速调试模式已启用（QUICK_MODE=1）")
        print(f"   新闻源: 最多 {MAX_SOURCES if MAX_SOURCES else '全部'} 个 | "
              f"每源扫描 {SCAN_ENTRIES} 条、精选 {MAX_PER_SOURCE} 条 | "
              f"学术模块: {'启用' if ENABLE_SCHOLAR else '跳过'}")
        print("=" * 60)
    fetch_news()
