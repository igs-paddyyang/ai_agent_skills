"""Skill Package 模板 + 範例 JSON + Sample Data"""

# ── 內建 Skill Package：crawler ──

SKILL_PKG_CRAWLER_PY = """\"\"\"Crawler Skill — ArkBot Skill Package 入口\"\"\"
import sys
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from crawler_skill import crawl_and_store
from intent_router import ArkBrain


def run(user_input: str) -> str:
    content = crawl_and_store(user_input)
    if content.startswith("❌"):
        return content
    brain = ArkBrain()
    summary = brain.summarize_content(content, user_input)
    return summary


if __name__ == "__main__":
    test_input = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    print(f"輸入：{test_input}")
    print(f"結果：{run(test_input)}")
"""

# ── 內建 Skill Package：chat ──

SKILL_PKG_CHAT_PY = """\"\"\"Chat Skill — ArkBot Skill Package 入口\"\"\"
import sys
from pathlib import Path

SRC_DIR = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from intent_router import ArkBrain


def run(user_input: str) -> str:
    brain = ArkBrain()
    return brain.chat(user_input)


if __name__ == "__main__":
    test_input = sys.argv[1] if len(sys.argv) > 1 else "你好"
    print(f"輸入：{test_input}")
    print(f"結果：{run(test_input)}")
"""

# ── Lite 版 Skill Package 模板 ──

SKILL_PKG_DASHBOARD_LITE_PY = """\"\"\"Dashboard Skill（Lite 版）— 使用 Gemini API 產出簡易 HTML 儀表板\"\"\"
import sys
import os
import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)
DASHBOARD_DIR = PROJECT_ROOT / "data" / "dashboard"


def run(user_input: str) -> str:
    \"\"\"同步入口 — 用 Gemini 產出簡易 HTML 儀表板\"\"\"
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    json_files = sorted(DASHBOARD_DIR.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    data_context = ""
    if json_files:
        try:
            with open(json_files[0], encoding="utf-8") as f:
                data_context = f.read()[:3000]
        except Exception:
            pass

    prompt = f\"\"\"根據以下資料產出一個簡潔的 HTML 儀表板頁面。
使用內嵌 CSS，不要外部依賴。包含 KPI 卡片和簡易表格。

使用者需求：{user_input}

資料（JSON）：
{data_context if data_context else '（無資料，請產出範例儀表板）'}
\"\"\"

    try:
        resp = client.models.generate_content(
            model=model, contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        html = resp.text or ""
        import re
        if html.startswith("```"):
            html = re.sub(r"^```\\w*\\n?", "", html)
            html = re.sub(r"\\n?```$", "", html)

        from datetime import datetime
        DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        html_path = DASHBOARD_DIR / f"dashboard_{ts}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return json.dumps({"summary": f"Dashboard generated: {html_path.name}", "html_path": str(html_path)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def run_async(user_input: str) -> dict:
    \"\"\"非同步入口\"\"\"
    result = run(user_input)
    data = json.loads(result)
    if "error" in data:
        return {"success": False, "error": data["error"]}
    return {"success": True, "result": data}
"""

SKILL_PKG_NOTIFY_LITE_PY = """\"\"\"Notify Skill — 發送 TG 通報（使用 notify_skill.send_to_route）\"\"\"
import sys
import json as _json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))
sys.path.insert(0, str(PROJECT_ROOT))


def run(user_input: str) -> str:
    \"\"\"同步入口\"\"\"
    from notify_skill import send_to_route
    route = "default"
    message = user_input
    if "|||" in user_input:
        parts = user_input.split("|||", 1)
        message = parts[0].strip()
        try:
            params = _json.loads(parts[1])
            route = params.get("route", route)
        except Exception:
            pass
    return send_to_route(message, route=route)


async def run_async(user_input: str) -> dict:
    \"\"\"非同步入口\"\"\"
    result = run(user_input)
    return {"success": True, "result": result}
"""

# ── 內建 Skill Package：dashboard（Task 6.4 新增）──

SKILL_PKG_DASHBOARD_PY = """\"\"\"Dashboard Skill — ArkBot Skill Package 入口\"\"\"
import sys
import json
import asyncio
from pathlib import Path

# 將 src/ 加入 path，以便引用 dashboard_skill 模組
SRC_DIR = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from dashboard_skill import generate_dashboard_from_input


def run(user_input: str) -> str:
    \"\"\"
    Executor 統一入口（同步）。
    內部用 asyncio.run() 包裝 async 函式。
    回傳 JSON 字串。
    \"\"\"
    result = asyncio.run(generate_dashboard_from_input(user_input))
    return json.dumps(result, ensure_ascii=False)


async def run_async(user_input: str) -> dict:
    \"\"\"
    Executor async 模式入口。
    直接回傳 dict，由 Executor 處理。
    \"\"\"
    return await generate_dashboard_from_input(user_input)


# 獨立測試：py skills/dashboard/skill.py "產生營收儀表板"
if __name__ == "__main__":
    test_input = sys.argv[1] if len(sys.argv) > 1 else "產生營收儀表板"
    print(f"輸入：{test_input}")
    result = run(test_input)
    print(f"結果：{result}")
"""

# ── Sample Data JSON ──

SAMPLE_REVENUE_JSON = '''{
  "title": "營收分析儀表板",
  "date": "2026-03-18",
  "source": "preprocessed_bklog.DailyUserInfoSnapshot",
  "kpi": [
    {"label": "活躍玩家數", "value": 28456},
    {"label": "總押注金額", "value": 15234567.89},
    {"label": "總贏分金額", "value": 14012345.67},
    {"label": "毛利率 (GGR%)", "value": "8.02%"},
    {"label": "總儲值金額", "value": 3456789.00},
    {"label": "ARPU", "value": 535.23}
  ],
  "trend": [
    {"date": "2026-03-12", "daily_bet": 14523456, "daily_win": 13245678, "active_users": 27123},
    {"date": "2026-03-13", "daily_bet": 15012345, "daily_win": 13856789, "active_users": 27856},
    {"date": "2026-03-14", "daily_bet": 16234567, "daily_win": 14923456, "active_users": 29012},
    {"date": "2026-03-15", "daily_bet": 15567890, "daily_win": 14234567, "active_users": 28345},
    {"date": "2026-03-16", "daily_bet": 14890123, "daily_win": 13678901, "active_users": 27890},
    {"date": "2026-03-17", "daily_bet": 15123456, "daily_win": 13901234, "active_users": 28123},
    {"date": "2026-03-18", "daily_bet": 15234567, "daily_win": 14012345, "active_users": 28456}
  ],
  "distribution": {
    "by_country": [
      {"country": "CN", "active_users": 12345, "daily_bet": 6234567, "daily_win": 5734567},
      {"country": "VN", "active_users": 5678, "daily_bet": 3123456, "daily_win": 2876543},
      {"country": "TW", "active_users": 4321, "daily_bet": 2345678, "daily_win": 2156789},
      {"country": "JP", "active_users": 3456, "daily_bet": 1890123, "daily_win": 1734567},
      {"country": "US", "active_users": 1234, "daily_bet": 890123, "daily_win": 812345},
      {"country": "OTHER", "active_users": 1422, "daily_bet": 750620, "daily_win": 697534}
    ],
    "by_vip": [
      {"vip_level": 0, "active_users": 15234, "daily_bet": 2345678, "total_deposit": 456789},
      {"vip_level": 1, "active_users": 6789, "daily_bet": 3456789, "total_deposit": 1234567},
      {"vip_level": 2, "active_users": 3456, "daily_bet": 4567890, "total_deposit": 2345678},
      {"vip_level": 3, "active_users": 1890, "daily_bet": 2890123, "total_deposit": 3456789},
      {"vip_level": 4, "active_users": 789, "daily_bet": 1234567, "total_deposit": 4567890},
      {"vip_level": 5, "active_users": 298, "daily_bet": 739520, "total_deposit": 5678901}
    ]
  }
}'''

SAMPLE_SLOTS_JSON = '''{
  "title": "老虎機分析儀表板",
  "date": "2026-03-18",
  "source": "bklog.SessionBetWinLog",
  "kpi": [
    {"label": "總場次數", "value": 456789},
    {"label": "總押注金額", "value": 12345678.90},
    {"label": "總贏分金額", "value": 11234567.80},
    {"label": "RTP", "value": "91.0%"},
    {"label": "平均每轉押注", "value": 27.03},
    {"label": "活躍玩家數", "value": 18234}
  ],
  "trend": [
    {"date": "2026-03-12", "total_bet": 11234567, "total_win": 10234567, "sessions": 423456},
    {"date": "2026-03-13", "total_bet": 11567890, "total_win": 10567890, "sessions": 434567},
    {"date": "2026-03-14", "total_bet": 12890123, "total_win": 11723456, "sessions": 467890},
    {"date": "2026-03-15", "total_bet": 12123456, "total_win": 11012345, "sessions": 445678},
    {"date": "2026-03-16", "total_bet": 11890123, "total_win": 10823456, "sessions": 438901},
    {"date": "2026-03-17", "total_bet": 12012345, "total_win": 10945678, "sessions": 441234},
    {"date": "2026-03-18", "total_bet": 12345678, "total_win": 11234567, "sessions": 456789}
  ],
  "top_games": [
    {"game_name": "Fortune Tiger", "total_bet": 2345678, "total_win": 2134567, "sessions": 89012, "rtp": "91.0%"},
    {"game_name": "Lucky Panda", "total_bet": 1890123, "total_win": 1723456, "sessions": 67890, "rtp": "91.2%"},
    {"game_name": "Dragon Gold", "total_bet": 1567890, "total_win": 1412345, "sessions": 56789, "rtp": "90.1%"},
    {"game_name": "Phoenix Rise", "total_bet": 1234567, "total_win": 1134567, "sessions": 45678, "rtp": "91.9%"},
    {"game_name": "Mystic Gems", "total_bet": 1012345, "total_win": 923456, "sessions": 34567, "rtp": "91.2%"},
    {"game_name": "Wild Safari", "total_bet": 890123, "total_win": 812345, "sessions": 28901, "rtp": "91.3%"},
    {"game_name": "Ocean King", "total_bet": 756789, "total_win": 689012, "sessions": 23456, "rtp": "91.0%"},
    {"game_name": "Star Burst", "total_bet": 678901, "total_win": 612345, "sessions": 21234, "rtp": "90.2%"},
    {"game_name": "Gold Rush", "total_bet": 567890, "total_win": 518901, "sessions": 18901, "rtp": "91.4%"},
    {"game_name": "Jade Emperor", "total_bet": 456789, "total_win": 415678, "sessions": 15678, "rtp": "91.0%"}
  ],
  "distribution": {
    "by_country": [
      {"country": "CN", "total_bet": 5234567, "total_win": 4756789, "sessions": 189012},
      {"country": "VN", "total_bet": 2567890, "total_win": 2345678, "sessions": 89012},
      {"country": "TW", "total_bet": 1890123, "total_win": 1712345, "sessions": 67890},
      {"country": "JP", "total_bet": 1345678, "total_win": 1223456, "sessions": 56789},
      {"country": "US", "total_bet": 789012, "total_win": 718901, "sessions": 28901},
      {"country": "OTHER", "total_bet": 518408, "total_win": 477398, "sessions": 25185}
    ],
    "by_vip": [
      {"vip_level": 0, "total_bet": 1890123, "total_win": 1723456, "avg_bet_per_spin": 12},
      {"vip_level": 1, "total_bet": 2567890, "total_win": 2334567, "avg_bet_per_spin": 20},
      {"vip_level": 2, "total_bet": 3234567, "total_win": 2945678, "avg_bet_per_spin": 35},
      {"vip_level": 3, "total_bet": 2456789, "total_win": 2234567, "avg_bet_per_spin": 50},
      {"vip_level": 4, "total_bet": 1345678, "total_win": 1223456, "avg_bet_per_spin": 80},
      {"vip_level": 5, "total_bet": 850631, "total_win": 772843, "avg_bet_per_spin": 120}
    ]
  }
}'''

SAMPLE_FISH_JSON = '''{
  "title": "魚機分析儀表板",
  "date": "2026-03-18",
  "source": "bklog.SessionTigerSharkBetWinLog",
  "kpi": [
    {"label": "總場次數", "value": 123456},
    {"label": "總押注金額", "value": 4567890.12},
    {"label": "總贏分金額", "value": 4123456.78},
    {"label": "RTP", "value": "90.3%"},
    {"label": "活躍玩家數", "value": 8901},
    {"label": "場均押注", "value": 36.99}
  ],
  "trend": [
    {"date": "2026-03-12", "total_bet": 4123456, "total_win": 3723456, "sessions": 112345},
    {"date": "2026-03-13", "total_bet": 4234567, "total_win": 3823456, "sessions": 115678},
    {"date": "2026-03-14", "total_bet": 4678901, "total_win": 4223456, "sessions": 126789},
    {"date": "2026-03-15", "total_bet": 4456789, "total_win": 4023456, "sessions": 121234},
    {"date": "2026-03-16", "total_bet": 4345678, "total_win": 3923456, "sessions": 118901},
    {"date": "2026-03-17", "total_bet": 4456789, "total_win": 4023456, "sessions": 120123},
    {"date": "2026-03-18", "total_bet": 4567890, "total_win": 4123456, "sessions": 123456}
  ],
  "top_games": [
    {"game_name": "Ocean King 3", "total_bet": 1234567, "total_win": 1112345, "sessions": 34567, "rtp": "90.1%"},
    {"game_name": "Tiger Shark", "total_bet": 890123, "total_win": 801234, "sessions": 23456, "rtp": "90.0%"},
    {"game_name": "Dragon Fisher", "total_bet": 678901, "total_win": 618901, "sessions": 18901, "rtp": "91.2%"},
    {"game_name": "Golden Toad", "total_bet": 567890, "total_win": 512345, "sessions": 15678, "rtp": "90.2%"},
    {"game_name": "Mermaid Legend", "total_bet": 456789, "total_win": 412345, "sessions": 12345, "rtp": "90.3%"},
    {"game_name": "Pirate Treasure", "total_bet": 345678, "total_win": 312345, "sessions": 9876, "rtp": "90.4%"},
    {"game_name": "Deep Sea Hunter", "total_bet": 234567, "total_win": 212345, "sessions": 5432, "rtp": "90.5%"},
    {"game_name": "Coral Reef", "total_bet": 159375, "total_win": 141596, "sessions": 3201, "rtp": "88.8%"}
  ],
  "distribution": {
    "by_country": [
      {"country": "CN", "total_bet": 1890123, "total_win": 1712345, "sessions": 45678},
      {"country": "VN", "total_bet": 1012345, "total_win": 912345, "sessions": 28901},
      {"country": "TW", "total_bet": 678901, "total_win": 612345, "sessions": 18901},
      {"country": "JP", "total_bet": 456789, "total_win": 412345, "sessions": 14567},
      {"country": "US", "total_bet": 289012, "total_win": 261234, "sessions": 8901},
      {"country": "OTHER", "total_bet": 240720, "total_win": 212842, "sessions": 6508}
    ],
    "by_vip": [
      {"vip_level": 0, "total_bet": 567890, "total_win": 512345, "players": 4567},
      {"vip_level": 1, "total_bet": 890123, "total_win": 801234, "players": 2012},
      {"vip_level": 2, "total_bet": 1234567, "total_win": 1112345, "players": 1234},
      {"vip_level": 3, "total_bet": 890123, "total_win": 801234, "players": 678},
      {"vip_level": 4, "total_bet": 567890, "total_win": 512345, "players": 289},
      {"vip_level": 5, "total_bet": 417297, "total_win": 383953, "players": 121}
    ]
  }
}'''


# ═══ ArkAgent OS YAML 版 Skill Package ═══

# ── 內建 Skill Package：notify（TG 通報骨架）──

SKILL_PKG_NOTIFY_YAML = '''type: skill
name: notify
version: 1.0.0
skill_id: notify
runtime: python
intent:
  - NOTIFY
description: "讀取 JSON 資料，格式化為 Telegram 通報訊息並發送至指定路由"
examples:
  - "發送今日營收通報"
  - "通報營收報告"
  - "TG 營收通知"
input:
  json_path:
    type: string
    required: false
execution:
  mode: async
  entry: skill.py
  timeout: 30
tags:
  - 通報
  - notify
  - telegram
priority: 5
enabled: true
response_type: text
'''

SKILL_PKG_NOTIFY_PY = """\"\"\"Notify Skill — 讀取 JSON 並發送 Telegram 通報

依據 config/telegram.json 的路由設定，自動偵測資料類型（營收/老虎機/魚機），
格式化為 TG 訊息並發送至指定群組/Topic。
\"\"\"
import sys
import json as _json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))
sys.path.insert(0, str(PROJECT_ROOT))


def run(user_input: str) -> str:
    \"\"\"同步入口 — Executor subprocess 模式呼叫\"\"\"
    import asyncio
    from notify_skill import send_revenue_notify
    result = asyncio.run(send_revenue_notify(user_input))
    return result


async def run_async(user_input: str) -> dict:
    \"\"\"非同步入口 — Executor async 模式呼叫，支援 Scheduler params\"\"\"
    from notify_skill import send_revenue_notify

    route = "default"
    actual_input = user_input

    # 支援 scheduler 傳入 params：input|||{"route":"daily_revenue"}
    if "|||" in user_input:
        parts = user_input.split("|||", 1)
        actual_input = parts[0].strip()
        try:
            params = _json.loads(parts[1])
            route = params.get("route", route)
        except Exception:
            pass

    result = await send_revenue_notify(actual_input, route=route)
    return {"success": True, "result": result}
"""

SKILL_PKG_CRAWLER_YAML = '''type: skill
name: crawler
version: 1.0.0
skill_id: crawler
runtime: python
intent:
  - RESEARCH
description: "網頁爬取與摘要，將指定 URL 的網頁內容爬取、轉換為 Markdown 並產出結構化摘要"
examples:
  - "幫我爬取這個網頁"
  - "https://example.com"
  - "擷取這個網站的資料並摘要"
input:
  url:
    type: string
    required: false
execution:
  mode: subprocess
  entry: skill.py
  timeout: 30
tags:
  - 爬蟲
  - 研究
  - 摘要
  - URL
  - crawl
  - scraper
  - research
priority: 10
enabled: true
'''

SKILL_PKG_CHAT_YAML = '''type: skill
name: chat
version: 1.0.0
skill_id: chat
runtime: python
intent:
  - CASUAL
description: "閒聊對話，友善自然地回應使用者的日常對話、打招呼、情緒表達"
examples:
  - "你好"
  - "今天天氣如何"
  - "謝謝你"
execution:
  mode: subprocess
  entry: skill.py
tags:
  - 閒聊
  - 聊天
  - chat
  - casual
priority: -1
enabled: true
'''

SKILL_PKG_DASHBOARD_YAML = '''type: skill
name: dashboard
version: 1.0.0
skill_id: dashboard
runtime: python
intent:
  - DASHBOARD
description: "產生數據儀表板（營收/老虎機/魚機），三層架構引擎（JSON → DSL → Renderer → HTML）"
examples:
  - "產生營收儀表板"
  - "幫我看昨天的老虎機數據"
  - "魚機分析"
  - "產生 2026-03-18 的營收分析儀表板"
  - "幫我用 data/dashboard/sample_slots.json 產生老虎機分析儀表板"
input:
  json_path:
    type: string
    required: false
  date:
    type: string
    required: false
  type:
    type: string
    required: false
execution:
  mode: async
  entry: skill.py
  timeout: 60
tags:
  - 儀表板
  - dashboard
  - 營收
  - 老虎機
  - 魚機
  - 圖表
  - revenue
  - slots
  - fish
priority: 10
enabled: true
response_type: dashboard
'''


# ═══ Gemini Canvas Skill Package（DASHBOARD_CANVAS 意圖）═══

SKILL_PKG_CANVAS_YAML = '''type: skill
name: gemini-canvas
version: 1.0.0
skill_id: gemini-canvas
runtime: python
intent:
  - DASHBOARD_CANVAS
description: "Gemini Canvas 儀表板 — 透過 Gemini API 直接產出 HTML（AI 自由排版，適合探索性分析）"
examples:
  - "用 AI 畫儀表板"
  - "gemini canvas dashboard"
  - "用 gemini 產生圖表"
  - "AI 自由排版儀表板"
  - "canvas 模式產生營收分析"
input:
  json_path:
    type: string
    required: false
  date:
    type: string
    required: false
execution:
  mode: async
  entry: skill.py
  timeout: 120
tags:
  - canvas
  - gemini
  - AI儀表板
  - 自由排版
priority: 5
enabled: true
response_type: dashboard
'''

SKILL_PKG_CANVAS_PY = """\"\"\"Gemini Canvas Dashboard Skill — ArkBot Skill Package 入口

使用 Gemini API 直接產出 HTML（gemini-canvas 模式）。
適合探索性分析、自由排版需求。
\"\"\"
import sys
import json
import asyncio
from pathlib import Path

# 將 src/ 加入 path，以便引用 gemini_canvas_skill 模組
SRC_DIR = str(Path(__file__).resolve().parent.parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from gemini_canvas_skill import generate_dashboard_from_input


def run(user_input: str) -> str:
    \"\"\"Executor 統一入口（同步）\"\"\"
    result = asyncio.run(generate_dashboard_from_input(user_input))
    return json.dumps(result, ensure_ascii=False)


async def run_async(user_input: str) -> dict:
    \"\"\"Executor async 模式入口\"\"\"
    return await generate_dashboard_from_input(user_input)


# 獨立測試：py skills/gemini-canvas/skill.py "用 AI 畫營收儀表板"
if __name__ == "__main__":
    test_input = sys.argv[1] if len(sys.argv) > 1 else "用 AI 畫營收儀表板"
    print(f"輸入：{test_input}")
    result = run(test_input)
    print(f"結果：{result}")
"""


# ═══ Composite Workflow Skill Package ═══

SKILL_PKG_DAILY_REPORT_YAML = '''type: skill
name: daily-report
version: 1.0.0
skill_id: daily-report
runtime: composite
intent:
  - DAILY_REPORT
description: "每日報告流程：爬取數據 → 產生儀表板 → 發送通報"
examples:
  - "產生每日報告"
  - "執行日報流程"
  - "daily report"
composite:
  strategy: sequential
  steps:
    - skill_id: crawler
      input_template: "{user_input}"
    - skill_id: dashboard
      input_template: "產生營收儀表板"
    - skill_id: notify
      input_template: "發送今日營收通報"
tags:
  - 每日報告
  - workflow
  - daily report
priority: 10
enabled: true
response_type: text
'''


# ═══ AIBI Skill Package（MCP / AI / Composite）═══

# ── MCP Skill：sql-query（本地 SQLite 查詢）──

SKILL_PKG_SQL_QUERY_YAML = '''type: skill
name: sql-query
version: 1.0.0
skill_id: sql-query
runtime: mcp
intent:
  - SQL_QUERY
description: "透過 MCP 連接本地 SQLite 資料庫，執行 SQL 查詢並回傳結構化結果"
examples:
  - "查詢昨天的活躍玩家數"
  - "SELECT COUNT(*) FROM daily_snapshot"
  - "幫我查營收前 10 的遊戲"
  - "查資料庫"
mcp:
  server: sqlite-server
  tool: query
  param_mapping:
    sql: "{user_input}"
tags:
  - SQL
  - 查詢
  - 資料庫
  - query
  - database
  - sqlite
priority: 8
enabled: true
response_type: text
'''

# ── MCP Skill：bigquery-query（Google BigQuery 查詢）──

SKILL_PKG_BIGQUERY_QUERY_YAML = '''type: skill
name: bigquery-query
version: 1.0.0
skill_id: bigquery-query
runtime: mcp
intent:
  - BIGQUERY
description: "透過 MCP 連接 Google BigQuery，執行 SQL 查詢大數據倉儲並回傳分析結果"
examples:
  - "查 BigQuery 昨天的營收"
  - "BQ 查詢活躍玩家趨勢"
  - "從 BigQuery 撈遊戲 RTP 數據"
  - "bigquery 查詢"
mcp:
  server: bigquery-server
  tool: execute-query
  param_mapping:
    query: "{user_input}"
tags:
  - BigQuery
  - BQ
  - 大數據
  - SQL
  - query
  - warehouse
priority: 8
enabled: true
response_type: text
'''

# ── MCP Skill：mssql-query（MSSQL 查詢）──

SKILL_PKG_MSSQL_QUERY_YAML = '''type: skill
name: mssql-query
version: 1.0.0
skill_id: mssql-query
runtime: mcp
intent:
  - MSSQL_QUERY
description: "透過 MCP 連接 MSSQL 資料庫，執行 SQL 查詢並回傳結構化結果"
examples:
  - "查 MSSQL 昨天的營收"
  - "SQL Server 查詢活躍玩家"
  - "從 MSSQL 撈遊戲 RTP 數據"
  - "mssql 查詢"
mcp:
  server: mssql-server
  tool: execute_sql
  param_mapping:
    query: "{user_input}"
tags:
  - MSSQL
  - SQL Server
  - 查詢
  - 資料庫
  - query
  - database
priority: 8
enabled: true
response_type: text
'''

# ── AI Skill：kpi-analyzer（KPI 異常分析）──

SKILL_PKG_KPI_ANALYZER_YAML = '''type: skill
name: kpi-analyzer
version: 1.0.0
skill_id: kpi-analyzer
runtime: ai
intent:
  - KPI_ANALYSIS
description: "分析 KPI 數據，偵測異常波動並產出分析報告（純 AI 推理，數據由上游 Skill 或使用者提供）"
examples:
  - "分析這份數據有沒有異常"
  - "KPI 有異常嗎"
  - "幫我看這些指標"
ai:
  model: gemini-2.5-flash
  prompt_file: prompt.txt
  temperature: 0.3
  max_tokens: 4096
  output_format: text
  fallback_skill: chat
tags:
  - KPI
  - 分析
  - anomaly
  - 異常偵測
priority: 5
enabled: true
response_type: text
'''

SKILL_PKG_KPI_ANALYZER_PROMPT = '''你是 AIBI 數據異常偵測專家。根據以下數據和使用者問題，分析是否存在異常。

## 分析規則
1. KPI 日環比波動超過 ±15% 視為異常
2. RTP 偏離基準值（91%）超過 ±3% 視為異常
3. 活躍玩家數日環比下降超過 10% 視為警告
4. 單一國家佔比突然變化超過 20% 視為異常
5. 毛利率（GGR%）低於 5% 視為警告，低於 0% 視為嚴重

## 輸出格式（繁體中文）

### 異常等級
- 🔴 嚴重：需要立即處理
- 🟡 警告：需要關注
- 🟢 正常：指標在合理範圍

### 異常項目
列出具體指標名稱、當前值、基準值、偏離幅度

### 可能原因
推測 2~3 個可能原因（活動影響、系統異常、季節性波動等）

### 建議行動
具體的後續步驟（查看哪些報表、通知哪些團隊、是否需要緊急處理）

## 對話記憶
{context}

## 使用者問題與數據
{user_input}
'''

# ── Composite Workflow：anomaly-report（異常偵測流程）──

SKILL_PKG_ANOMALY_REPORT_YAML = '''type: skill
name: anomaly-report
version: 1.0.0
skill_id: anomaly-report
runtime: composite
intent:
  - ANOMALY_DETECT
description: "數據異常偵測流程：產生儀表板取得 KPI → AI 分析異常 → 產出報告"
examples:
  - "檢查昨天的數據有沒有異常"
  - "分析營收波動"
  - "偵測 RTP 異常"
  - "異常偵測"
composite:
  strategy: sequential
  steps:
    - skill_id: dashboard
      input_template: "產生營收儀表板"
    - skill_id: kpi-analyzer
      input_template: "根據以下儀表板產出結果，分析是否有 KPI 異常：{prev_result}"
tags:
  - 異常偵測
  - anomaly
  - 監控
  - KPI
  - workflow
priority: 8
enabled: true
response_type: text
'''

# ── TG 通報樣板（notify/assets/）──

TG_FORMATTER_PY = '''"""TG 通報訊息格式化器 — 讀取 assets/ 樣板，填入資料產出 TG 訊息"""
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent

COUNTRY_FLAGS = {
    "CN": "\\U0001f1e8\\U0001f1f3", "JP": "\\U0001f1ef\\U0001f1f5",
    "TW": "\\U0001f1f9\\U0001f1fc", "VN": "\\U0001f1fb\\U0001f1f3",
    "US": "\\U0001f1fa\\U0001f1f8", "KR": "\\U0001f1f0\\U0001f1f7",
}
MEDALS = ["\\U0001f947", "\\U0001f948", "\\U0001f949", "\\U0001f539", "\\U0001f539"]


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _fmt_big(value) -> str:
    v = float(value) if value else 0
    if v >= 1e12:
        return f"{v / 1e12:,.2f}T"
    elif v >= 1e9:
        return f"{v / 1e9:,.2f}B"
    elif v >= 1e6:
        return f"{v / 1e6:,.2f}M"
    elif v >= 1e3:
        return f"{v / 1e3:,.1f}K"
    else:
        return f"{v:,.2f}"


def _format_date(d) -> str:
    s = str(d)
    if "-" in s:
        return s[:10]
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"


def format_revenue_message(data: dict) -> str:
    template = (ASSETS_DIR / "tg_revenue_template.txt").read_text(encoding="utf-8")
    markets = data.get("markets", [])
    market_lines = []
    for m in markets[:5]:
        flag = COUNTRY_FLAGS.get(m["country"], "\\U0001f310")
        market_lines.append(f"{flag} {m[\\'country\\']}: ${_fmt(m[\\'revenue\\'])} (\\U0001f464 {m[\\'users\\']}人)")

    top_player_lines = []
    for i, p in enumerate(data.get("top_players", [])[:5]):
        medal = MEDALS[i] if i < len(MEDALS) else "\\U0001f539"
        top_player_lines.append(f"{medal} UID {p[\\'uid\\']}: ${_fmt(p[\\'revenue\\'])}")

    return template.format(
        date=_format_date(data.get("date", "")),
        total_revenue=_fmt(data.get("total_revenue", 0)),
        total_users=_fmt(data.get("total_users", 0)),
        market_lines="\\n".join(market_lines) or "（無資料）",
        top_player_lines="\\n".join(top_player_lines) or "（無資料）",
    )


def format_game_message(data: dict) -> str:
    template = (ASSETS_DIR / "tg_game_template.txt").read_text(encoding="utf-8")
    slots = data.get("slot_games", [])
    slot_bet = sum(g.get("total_bet", 0) for g in slots)
    slot_win = sum(g.get("total_win", 0) for g in slots)
    slot_rtp = f"{slot_win / slot_bet * 100:.2f}" if slot_bet > 0 else "N/A"
    slot_sessions = sum(g.get("sessions", 0) for g in slots)
    slot_users = sum(g.get("users", 0) for g in slots)

    slot_sorted = sorted(slots, key=lambda g: g.get("total_bet", 0), reverse=True)
    slot_top5_lines = []
    for i, g in enumerate(slot_sorted[:5]):
        medal = MEDALS[i] if i < len(MEDALS) else "\\U0001f539"
        name = g.get("game_name", f"GameID={g.get(\\'game_id\\', \\'?\\')}")
        rtp = f"{g[\\'total_win\\'] / g[\\'total_bet\\'] * 100:.1f}" if g.get("total_bet", 0) > 0 else "N/A"
        slot_top5_lines.append(f"{medal} {name}: {_fmt_big(g.get(\\'total_bet\\', 0))} | RTP {rtp}%")

    markets = data.get("country_distribution", [])
    market_lines = []
    for m in markets[:6]:
        flag = COUNTRY_FLAGS.get(m.get("country", ""), "\\U0001f310")
        market_lines.append(f"{flag} {m.get(\\'country\\', \\'?\\')} : {_fmt_big(m.get(\\'total_bet\\', 0))} | \\U0001f464 {_fmt(m.get(\\'users\\', 0))}人")

    return template.format(
        date=_format_date(data.get("report_date", "")),
        slot_sessions=_fmt(slot_sessions),
        slot_users=_fmt(slot_users),
        slot_count=len(slots),
        slot_bet=_fmt_big(slot_bet),
        slot_rtp=slot_rtp,
        total_bet=_fmt_big(slot_bet),
        total_rtp=slot_rtp,
        slot_top5_lines="\\n".join(slot_top5_lines) or "（無資料）",
        market_lines="\\n".join(market_lines) or "（無資料）",
    )
'''

TG_REVENUE_TEMPLATE = """📊 每日營收報告
⏰ 數據時間：{date}

🌍 1. 各市場營收表現
💰 總營收: ${total_revenue} (👤 {total_users}人)
{market_lines}

🏆 2. 玩家儲值排行榜 (Top 5)
{top_player_lines}
"""

TG_GAME_TEMPLATE = """🎮 每日遊戲分析報告
⏰ 數據時間：{date} 00:00-23:59

🎰 1. 老虎機總覽
🎲 場次: {slot_sessions} | 👤 玩家: {slot_users} | 🎮 {slot_count} 款
💰 押量: {slot_bet} | 🏆 RTP: {slot_rtp}%

📊 2. 整體 KPI
💰 總押量: {total_bet} | 🏆 整體 RTP: {total_rtp}%

🏆 3. 老虎機熱門 Top 5
{slot_top5_lines}

🌍 4. 各市場押量分佈
{market_lines}
"""
