"""入口層模板 — BOT_MAIN_PY, TELEGRAM_ENTRY_PY, WEB_SERVER_PY, WEB_ENTRY_PY, WEB_INDEX_HTML, CLI_ENTRY_PY"""

# bot_main.py 模板（含重試策略、proxy 支援、路徑修正）
BOT_MAIN_PY = r'''"""ArkBot Telegram 主程式"""
import os
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TimedOut, NetworkError
from dotenv import load_dotenv

# 以 src/ 的上一層為專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from intent_router import ArkBrain
from crawler_skill import crawl_and_store
from format_utils import escape_markdown_v2

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 重試策略：ConnectionError → 重試；ReadTimeout → 不重試
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

brain = ArkBrain()


async def _send_with_retry(coro_fn, *args, **kwargs):
    """ConnectionError/ConnectTimeout → 指數退避重試；ReadTimeout → 不重試。"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except TimedOut as e:
            cause = str(e.__cause__) if e.__cause__ else ""
            if "ConnectTimeout" in cause or "ConnectError" in cause:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"連線逾時，{delay}s 後重試 ({attempt+1}/{MAX_RETRIES})...")
                    await asyncio.sleep(delay)
                    continue
            raise
        except NetworkError as e:
            cause = str(e.__cause__) if e.__cause__ else str(e)
            if "ConnectError" in cause or "ConnectTimeout" in cause:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"連線失敗，{delay}s 後重試 ({attempt+1}/{MAX_RETRIES})：{cause}")
                    await asyncio.sleep(delay)
                    continue
            raise


async def start(update: Update, context):
    """歡迎訊息 — 靜態字串已手動跳脫 MarkdownV2 保留字元。"""
    welcome = (
        "🚀 *ArkBot 智庫助理* \(v1\.0\)\n\n"
        "傳送網址給我，我會幫你獵取並摘要內容\!\n"
        "也可以直接跟我聊天 🗣️"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN_V2)


async def handle_message(update: Update, context):
    """訊息處理 — 意圖分流核心邏輯，含連線重試。"""
    user_input = update.message.text

    try:
        thinking = await _send_with_retry(
            update.message.reply_text,
            "🧠 正在思考\.\.\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except (TimedOut, NetworkError) as e:
        logger.error(f"無法發送訊息：{e}")
        return

    intent = brain.classify_intent(user_input)

    if intent["intent"] == "RESEARCH" and intent.get("url"):
        url = intent["url"]
        try:
            await _send_with_retry(thinking.edit_text, "🔍 獵取中\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
        except (TimedOut, NetworkError):
            pass

        content = crawl_and_store(url)

        try:
            await _send_with_retry(thinking.edit_text, "📄 摘要生成中\.\.\.", parse_mode=ParseMode.MARKDOWN_V2)
        except (TimedOut, NetworkError):
            pass

        summary = brain.summarize_content(content, user_input)
        safe_text = escape_markdown_v2(summary)
        try:
            await _send_with_retry(thinking.edit_text, safe_text, parse_mode=ParseMode.MARKDOWN_V2)
        except (TimedOut, NetworkError) as e:
            logger.error(f"無法發送摘要結果：{e}")
    else:
        reply = brain.chat(user_input)
        safe_text = escape_markdown_v2(reply)
        try:
            await _send_with_retry(thinking.edit_text, safe_text, parse_mode=ParseMode.MARKDOWN_V2)
        except (TimedOut, NetworkError) as e:
            logger.error(f"無法發送閒聊回覆：{e}")


def main():
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    builder = (
        Application.builder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
    )
    if proxy:
        builder = builder.proxy(proxy).get_updates_proxy(proxy)
    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 ArkBot 已啟動！")
    if proxy:
        print(f"   使用代理：{proxy}")
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    main()
'''


# ── entry/telegram_entry.py（ArkAgent OS Telegram 入口 — 整合 Hybrid Router + Executor）──
TELEGRAM_ENTRY_PY = r'''"""ArkAgent Telegram 主程式 — 整合 Hybrid Router + Executor"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import TimedOut, NetworkError
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from arkbot_core import process_message
from format_utils import escape_markdown_v2

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2


async def _send_with_retry(coro_fn, *args, **kwargs):
    """ConnectionError/ConnectTimeout -> exponential backoff retry"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await coro_fn(*args, **kwargs)
        except TimedOut as e:
            cause = str(e.__cause__) if e.__cause__ else ""
            if "ConnectTimeout" in cause or "ConnectError" in cause:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"連線逾時，{delay}s 後重試 ({attempt+1}/{MAX_RETRIES})...")
                    await asyncio.sleep(delay)
                    continue
            raise
        except NetworkError as e:
            cause = str(e.__cause__) if e.__cause__ else str(e)
            if "ConnectError" in cause or "ConnectTimeout" in cause:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY_BASE ** (attempt + 1)
                    logger.warning(f"連線失敗，{delay}s 後重試 ({attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue
            raise


async def start(update: Update, context):
    """歡迎訊息"""
    welcome = (
        "\\*ArkAgent 智庫助理\\* \\(v1\\.0\\)\n\n"
        "傳送網址給我，我會幫你獵取並摘要內容\\!\n"
        "也可以直接跟我聊天"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN_V2)


async def handle_message(update: Update, context):
    """訊息處理 — 透過 process_message() 統一流程（與 Web 一致）"""
    user_input = update.message.text

    try:
        thinking = await _send_with_retry(
            update.message.reply_text,
            "正在思考\\.\\.\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except (TimedOut, NetworkError) as e:
        logger.error(f"無法發送訊息：{e}")
        return

    try:
        final_reply = ""
        async for event in process_message(user_input):
            if event["type"] == "status":
                try:
                    safe = escape_markdown_v2(event["content"])
                    await _send_with_retry(thinking.edit_text, safe, parse_mode=ParseMode.MARKDOWN_V2)
                except (TimedOut, NetworkError):
                    pass
            elif event["type"] == "reply":
                final_reply = event["content"]
            elif event["type"] == "dashboard":
                final_reply = event["content"]
                if event.get("html_path"):
                    # 顯示相對路徑（從 data/dashboard/ 開始）
                    hp = event["html_path"]
                    marker = "data/dashboard/"
                    idx = hp.find(marker)
                    rel = hp[idx:] if idx >= 0 else hp
                    final_reply += f"\n\n[dashboard] {rel}"
            elif event["type"] == "error":
                final_reply = f"[error] {event['content']}"

        if final_reply:
            safe = escape_markdown_v2(final_reply)
            try:
                await _send_with_retry(thinking.edit_text, safe, parse_mode=ParseMode.MARKDOWN_V2)
            except (TimedOut, NetworkError) as e:
                logger.error(f"無法發送回覆：{e}")
    except Exception as e:
        logger.error(f"處理失敗：{e}")
        try:
            await _send_with_retry(thinking.edit_text, f"處理失敗: {str(e)}")
        except (TimedOut, NetworkError):
            pass


def main():
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    builder = (
        Application.builder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
    )
    if proxy:
        builder = builder.proxy(proxy).get_updates_proxy(proxy)
    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("[Bot] ArkAgent Telegram 已啟動")
    if proxy:
        print(f"   proxy: {proxy}")
    app.run_polling(bootstrap_retries=5)


if __name__ == "__main__":
    main()
'''


# web_server.py 模板（含 /dashboard、dashboard_reply、Skill API）— ArkBot Foundation 版
WEB_SERVER_PY = r'''"""ArkBot Web 伺服器 — FastAPI + WebSocket 對話介面 + Skill API"""
import os
import glob
import json
import time
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from arkbot_core import process_message
from hybrid_router import registry
from executor import Executor

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ArkBot Web", version="1.0")
WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"
DASHBOARD_DIR = DATA_DIR / "dashboard"

# ── Skill API 設定 ──
SKILL_API_KEY = os.getenv("SKILL_API_KEY", "")
_skill_dir = str(PROJECT_ROOT / "skills")
_api_executor = Executor(registry, _skill_dir)


class SkillRequest(BaseModel):
    """Skill API 請求格式"""
    input: str
    params: dict = {}


def _verify_api_key(x_api_key: str | None):
    """驗證 API Key"""
    if not SKILL_API_KEY:
        raise HTTPException(status_code=500, detail="SKILL_API_KEY 未設定")
    if not x_api_key or x_api_key != SKILL_API_KEY:
        raise HTTPException(status_code=401, detail="無效的 API Key")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = WEB_DIR / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(file: str = Query(default=None, description="HTML 檔名")):
    """儀表板 HTML，支援 ?file=dashboard_xxx.html"""
    if file:
        html_path = DASHBOARD_DIR / file
    else:
        pattern = str(DASHBOARD_DIR / "dashboard_*.html")
        files = sorted(glob.glob(pattern), reverse=True)
        html_path = Path(files[0]) if files else None

    if html_path and html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse(
        "<h1>尚未產生儀表板</h1><p>請在對話中輸入「產生儀表板」觸發產生。</p>",
        status_code=404,
    )


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket 連線已建立")
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                user_input = msg.get("content", "").strip()
            except json.JSONDecodeError:
                user_input = data.strip()

            if not user_input:
                await ws.send_json({"type": "reply", "content": "請輸入訊息或網址 🚀"})
                continue

            try:
                async for event in process_message(user_input):
                    if event["type"] == "dashboard":
                        html_name = os.path.basename(event.get("html_path", ""))
                        await ws.send_json({
                            "type": "dashboard_reply",
                            "content": event["content"],
                            "dashboard_url": f"/dashboard?file={html_name}",
                        })
                    else:
                        await ws.send_json(event)
            except Exception as e:
                logger.error(f"處理失敗：{e}")
                await ws.send_json({"type": "error", "content": f"處理失敗: {str(e)}"})

    except WebSocketDisconnect:
        logger.info("WebSocket 連線已斷開")
    except Exception as e:
        logger.error(f"WebSocket 錯誤：{e}")
        try:
            await ws.send_json({"type": "error", "content": f"伺服器錯誤：{str(e)}"})
        except Exception:
            pass


# ═══ Skill API 端點 ═══

@app.get("/api/skills")
async def list_skills(x_api_key: str | None = Header(default=None)):
    """回傳所有已註冊 Skill 列表"""
    _verify_api_key(x_api_key)
    skills = [
        {
            "skill_id": s["skill_id"],
            "description": s["description"],
            "intent": s["intent"],
            "enabled": s.get("enabled", True),
            "mode": s.get("mode", "subprocess"),
            "tags": s.get("tags", []),
        }
        for s in registry.skills.values()
    ]
    return {"skills": skills, "count": len(skills)}


@app.post("/api/skill/{skill_id}")
async def execute_skill(
    skill_id: str,
    req: SkillRequest,
    x_api_key: str | None = Header(default=None),
):
    """直接執行指定 Skill，不經意圖分類"""
    _verify_api_key(x_api_key)

    meta = registry.get_skill(skill_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' 不存在")
    if not meta.get("enabled", True):
        raise HTTPException(status_code=400, detail=f"Skill '{skill_id}' 已停用")

    start = time.time()
    result = await _api_executor.execute(skill_id, req.input)
    elapsed_ms = int((time.time() - start) * 1000)

    return {
        "success": result.get("success", False),
        "skill_id": skill_id,
        "result": result.get("result", result.get("error", "")),
        "execution_time_ms": elapsed_ms,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEB_PORT", "2141"))
    print(f"🌐 ArkBot Web 啟動中：http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
'''


# ── entry/web_entry.py（ArkAgent OS Web 入口 — sys.path 修正 + Dashboard Hub API + 類型分目錄）──
WEB_ENTRY_PY = r'''"""ArkAgent Web 伺服器 — FastAPI + WebSocket 對話介面 + Skill API"""
import os
import glob
import json
import re
import time
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

import sys
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))
sys.path.insert(0, str(PROJECT_ROOT))

from arkbot_core import process_message
from hybrid_router import registry
from executor import Executor

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ArkAgent Web", version="1.0")
WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"
DASHBOARD_DIR = DATA_DIR / "dashboard"

# ── Skill API 設定 ──
SKILL_API_KEY = os.getenv("SKILL_API_KEY", "")
_skill_dir = str(PROJECT_ROOT / "skills")
_api_executor = Executor(registry, _skill_dir)


class SkillRequest(BaseModel):
    """Skill API 請求格式"""
    input: str
    params: dict = {}


def _verify_api_key(x_api_key: str | None):
    """驗證 API Key"""
    if not SKILL_API_KEY:
        raise HTTPException(status_code=500, detail="SKILL_API_KEY 未設定")
    if not x_api_key or x_api_key != SKILL_API_KEY:
        raise HTTPException(status_code=401, detail="無效的 API Key")


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = WEB_DIR / "index.html"
    return html_path.read_text(encoding="utf-8")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_hub():
    """報告中心入口"""
    hub_path = WEB_DIR / "dashboard_hub.html"
    if hub_path.exists():
        return hub_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>報告中心頁面不存在</h1>", status_code=500)


@app.get("/dashboard/view", response_class=HTMLResponse)
async def dashboard_view(file: str = Query(description="HTML 相對路徑，如 revenue/2026-03-18_093000.html")):
    """檢視單一儀表板 HTML（支援子目錄路徑）"""
    safe_path = Path(file)
    if ".." in safe_path.parts:
        return HTMLResponse("<h1>無效路徑</h1>", status_code=400)
    html_path = DASHBOARD_DIR / safe_path
    if html_path.exists() and html_path.is_file():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse(
        "<h1>找不到儀表板</h1><p>請確認檔案名稱是否正確。</p>",
        status_code=404,
    )


@app.delete("/api/dashboards/{dtype}/{filename}")
async def archive_dashboard(dtype: str, filename: str):
    """備份移除儀表板（移至 archive/ 子目錄）"""
    src = DASHBOARD_DIR / dtype / filename
    if not src.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    archive_dir = DASHBOARD_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    dst = archive_dir / f"{dtype}_{filename}"
    src.rename(dst)
    logger.info(f"儀表板已備份移除：{dtype}/{filename} → archive/")
    return {"success": True, "message": f"{dtype}/{filename} 已移至 archive/"}


@app.get("/api/dashboards")
async def list_dashboards():
    """回傳所有儀表板清單（掃描 revenue/slots/fish 子目錄）"""
    TYPE_DIRS = ["revenue", "slots", "fish"]
    dashboards = []
    for dtype in TYPE_DIRS:
        type_dir = DASHBOARD_DIR / dtype
        if not type_dir.is_dir():
            continue
        for p in type_dir.iterdir():
            if not p.is_file() or p.suffix != ".html":
                continue
            name = p.name
            m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})\.html", name)
            if m:
                date_str = m.group(1)
                time_str = f"{m.group(2)}:{m.group(3)}:{m.group(4)}"
            else:
                date_str = "unknown"
                time_str = "unknown"
            dashboards.append({
                "file": f"{dtype}/{name}",
                "date": date_str,
                "time": time_str,
                "type": dtype,
                "size_kb": round(p.stat().st_size / 1024, 1),
            })
    dashboards.sort(key=lambda x: x["file"], reverse=True)
    return {"dashboards": dashboards, "count": len(dashboards)}


@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket 連線已建立")
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                user_input = msg.get("content", "").strip()
            except json.JSONDecodeError:
                user_input = data.strip()

            if not user_input:
                await ws.send_json({"type": "reply", "content": "請輸入訊息或網址"})
                continue

            try:
                async for event in process_message(user_input):
                    if event["type"] == "dashboard":
                        html_path = event.get("html_path", "")
                        try:
                            rel = str(Path(html_path).relative_to(DASHBOARD_DIR))
                        except ValueError:
                            rel = os.path.basename(html_path)
                        await ws.send_json({
                            "type": "dashboard_reply",
                            "content": event["content"],
                            "dashboard_url": f"/dashboard/view?file={rel}",
                        })
                    else:
                        await ws.send_json(event)
            except Exception as e:
                logger.error(f"處理失敗：{e}")
                await ws.send_json({"type": "error", "content": f"處理失敗: {str(e)}"})

    except WebSocketDisconnect:
        logger.info("WebSocket 連線已斷開")
    except Exception as e:
        logger.error(f"WebSocket 錯誤：{e}")
        try:
            await ws.send_json({"type": "error", "content": f"伺服器錯誤：{str(e)}"})
        except Exception:
            pass


# ═══ Skill API 端點 ═══

@app.get("/api/skills")
async def list_skills(x_api_key: str | None = Header(default=None)):
    """回傳所有已註冊 Skill 列表"""
    _verify_api_key(x_api_key)
    skills = [
        {
            "skill_id": s["skill_id"],
            "description": s["description"],
            "intent": s["intent"],
            "enabled": s.get("enabled", True),
            "mode": s.get("mode", "subprocess"),
            "tags": s.get("tags", []),
        }
        for s in registry.skills.values()
    ]
    return {"skills": skills, "count": len(skills)}


@app.post("/api/skill/{skill_id}")
async def execute_skill(
    skill_id: str,
    req: SkillRequest,
    x_api_key: str | None = Header(default=None),
):
    """直接執行指定 Skill，不經意圖分類"""
    _verify_api_key(x_api_key)

    meta = registry.get_skill(skill_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' 不存在")
    if not meta.get("enabled", True):
        raise HTTPException(status_code=400, detail=f"Skill '{skill_id}' 已停用")

    start = time.time()
    result = await _api_executor.execute(skill_id, req.input)
    elapsed_ms = int((time.time() - start) * 1000)

    return {
        "success": result.get("success", False),
        "skill_id": skill_id,
        "result": result.get("result", result.get("error", "")),
        "execution_time_ms": elapsed_ms,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEB_PORT", "2141"))
    print(f"[Web] ArkAgent Web 啟動中：http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
'''


# web/index.html fallback 最小版本（含 dashboard_reply 支援）
WEB_INDEX_HTML = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ArkBot</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>.chat-bubble{max-width:80%;word-wrap:break-word}.chat-bubble pre{background:#1e293b;color:#e2e8f0;padding:12px;border-radius:8px;overflow-x:auto}.status-pulse{animation:pulse 1.5s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}</style>
</head>
<body class="bg-gray-900 text-gray-100 h-screen flex flex-col">
<header class="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center gap-3">
<span class="text-2xl">🚀</span><div><h1 class="text-lg font-semibold">ArkBot</h1><p class="text-xs text-gray-400" id="s">🔴 未連線</p></div>
</header>
<main id="m" class="flex-1 overflow-y-auto px-4 py-6 space-y-4"></main>
<footer class="bg-gray-800 border-t border-gray-700 px-4 py-3">
<form id="f" class="flex gap-3 max-w-4xl mx-auto">
<input id="i" type="text" placeholder="輸入訊息或網址..." class="flex-1 bg-gray-700 border border-gray-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500" autocomplete="off"/>
<button type="submit" class="bg-blue-600 hover:bg-blue-500 rounded-xl px-6 py-3 text-sm font-medium" id="b">發送</button>
</form></footer>
<script>
const m=document.getElementById("m"),f=document.getElementById("f"),i=document.getElementById("i"),b=document.getElementById("b"),s=document.getElementById("s");
let ws,sb;
function eh(t){const d=document.createElement("div");d.textContent=t;return d.innerHTML}
function cn(){const p=location.protocol==="https:"?"wss:":"ws:";ws=new WebSocket(`${p}//${location.host}/ws/chat`);
ws.onopen=()=>{s.textContent="🟢 已連線";b.disabled=false};
ws.onclose=()=>{s.textContent="🔴 已斷線";b.disabled=true;setTimeout(cn,3000)};
ws.onmessage=e=>{const d=JSON.parse(e.data);
if(d.type==="status"){if(!sb)sb=ab("bot",d.content,true);else sb.innerHTML=`<span class="status-pulse">${eh(d.content)}</span>`}
else if(d.type==="reply"){if(sb){sb.innerHTML=marked.parse(d.content);sb=null}else ab("bot",d.content,false,true);b.disabled=false;i.focus()}
else if(d.type==="dashboard_reply"){
const html=marked.parse(d.content)+'<br><a href="'+d.dashboard_url+'" target="_blank" class="inline-block mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">📊 開啟儀表板</a>';
if(sb){sb.innerHTML=html;sb=null}else{ab("bot","");m.lastElementChild.querySelector(".chat-bubble").innerHTML=html}
b.disabled=false;i.focus()}
else if(d.type==="error"){ab("bot","❌ "+d.content);sb=null;b.disabled=false}
m.scrollTop=m.scrollHeight}}
function ab(r,c,st=false,md=false){const w=document.createElement("div");w.className=`flex ${r==="user"?"justify-end":"justify-start"}`;
const bb=document.createElement("div");bb.className=r==="user"?"chat-bubble bg-blue-600 rounded-2xl rounded-tr-sm px-4 py-3 text-sm":"chat-bubble bg-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 text-sm";
if(st)bb.innerHTML=`<span class="status-pulse">${eh(c)}</span>`;else if(md)bb.innerHTML=marked.parse(c);else bb.textContent=c;
w.appendChild(bb);m.appendChild(w);m.scrollTop=m.scrollHeight;return bb}
f.addEventListener("submit",e=>{e.preventDefault();const t=i.value.trim();if(!t||!ws||ws.readyState!==1)return;
ab("user",t);ws.send(JSON.stringify({type:"message",content:t}));i.value="";b.disabled=true;sb=null});
cn();
</script></body></html>
'''


# ── entry/cli_entry.py（ArkAgent OS CLI 互動入口）──
CLI_ENTRY_PY = '''"""ArkAgent CLI 互動入口 — 終端對話模式"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from arkbot_core import process_message


async def main():
    print("[CLI] ArkAgent CLI 模式（輸入 quit 離開）")
    print("=" * 50)

    while True:
        try:
            user_input = input("\\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\n再見！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("再見！")
            break

        async for event in process_message(user_input):
            if event["type"] == "status":
                print(f"  [status] {event['content']}")
            elif event["type"] == "reply":
                print(f"\\n助理：{event['content']}")
            elif event["type"] == "dashboard":
                print(f"\\n助理：{event['content']}")
                print(f"  [dashboard] {event.get('html_path', '')}")
            elif event["type"] == "error":
                print(f"\\n[error] {event['content']}")


if __name__ == "__main__":
    asyncio.run(main())
'''


# ── web/dashboard_hub.html（報告中心入口頁）──
DASHBOARD_HUB_HTML = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArkAgent 數據中心</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card-hover { transition: transform 0.2s, box-shadow 0.2s; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen flex flex-col">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <span class="text-2xl">📊</span>
            <div>
                <h1 class="text-lg font-semibold">ArkAgent 數據中心</h1>
                <p class="text-xs text-gray-400">儀表板報告管理</p>
            </div>
        </div>
        <a href="/" class="text-sm text-blue-400 hover:text-blue-300 transition-colors">← 回到對話</a>
    </header>

    <!-- Filters -->
    <section class="bg-gray-800/50 border-b border-gray-700 px-6 py-4">
        <div class="max-w-6xl mx-auto flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
                <label class="text-sm text-gray-400">日期</label>
                <input type="date" id="filter-date"
                    class="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:border-blue-500" />
            </div>
            <div class="flex items-center gap-2">
                <label class="text-sm text-gray-400">類型</label>
                <select id="filter-type"
                    class="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm
                           focus:outline-none focus:border-blue-500">
                    <option value="all">全部</option>
                    <option value="revenue">營收</option>
                    <option value="slots">老虎機</option>
                    <option value="fish">魚機</option>
                    <option value="general">其他</option>
                </select>
            </div>
            <button id="btn-refresh" onclick="loadDashboards()"
                class="bg-blue-600 hover:bg-blue-500 rounded-lg px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2">
                <span id="refresh-icon">🔄</span> 更新清單
            </button>
            <span id="count-badge" class="text-xs text-gray-500 ml-auto"></span>
        </div>
    </section>

    <!-- Dashboard Grid -->
    <main class="flex-1 px-6 py-6">
        <div id="grid" class="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        </div>
        <div id="empty-state" class="hidden text-center py-20 text-gray-500">
            <p class="text-4xl mb-3">📭</p>
            <p>尚無儀表板，透過對話產生第一份報告吧</p>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 border-t border-gray-700 px-6 py-3 text-center text-xs text-gray-500">
        ArkAgent 數據中心 — Powered by ArkBot Generator
    </footer>

    <script>
    const TYPE_LABELS = { revenue: \'營收\', slots: \'老虎機\', fish: \'魚機\', general: \'其他\' };
    const TYPE_COLORS = {
        revenue: \'bg-green-600\', slots: \'bg-purple-600\',
        fish:    \'bg-cyan-600\',  general: \'bg-gray-600\',
    };

    let allDashboards = [];

    async function loadDashboards() {
        const icon = document.getElementById(\'refresh-icon\');
        icon.innerHTML = \'<span class="spin inline-block">⏳</span>\';
        try {
            const res = await fetch(\'/api/dashboards\');
            const data = await res.json();
            allDashboards = data.dashboards || [];
            applyFilters();
        } catch (e) {
            console.error(\'載入失敗\', e);
        } finally {
            icon.textContent = \'🔄\';
        }
    }

    function applyFilters() {
        const dateVal = document.getElementById(\'filter-date\').value;
        const typeVal = document.getElementById(\'filter-type\').value;

        let filtered = allDashboards;
        if (dateVal) filtered = filtered.filter(d => d.date === dateVal);
        if (typeVal !== \'all\') filtered = filtered.filter(d => d.type === typeVal);

        renderGrid(filtered);
    }

    function renderGrid(list) {
        const grid = document.getElementById(\'grid\');
        const empty = document.getElementById(\'empty-state\');
        const badge = document.getElementById(\'count-badge\');

        badge.textContent = `共 ${list.length} / ${allDashboards.length} 份`;

        if (list.length === 0) {
            grid.innerHTML = \'\';
            empty.classList.remove(\'hidden\');
            return;
        }
        empty.classList.add(\'hidden\');

        grid.innerHTML = list.map(d => `
            <div class="card-hover bg-gray-800 border border-gray-700 rounded-xl p-5 relative">
                <a href="/dashboard/view?file=${encodeURIComponent(d.file)}" target="_blank" class="block cursor-pointer">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs px-2 py-1 rounded-full text-white ${TYPE_COLORS[d.type] || \'bg-gray-600\'}">
                            ${TYPE_LABELS[d.type] || d.type}
                        </span>
                        <span class="text-xs text-gray-500">${d.size_kb} KB</span>
                    </div>
                    <p class="text-sm font-medium text-gray-200 mb-1">${d.date}</p>
                    <p class="text-xs text-gray-400">${d.time}</p>
                    <p class="text-xs text-gray-600 mt-2 truncate">${d.file}</p>
                </a>
                <button onclick="archiveDashboard(\'${d.file}\')" title="備份移除"
                    class="absolute bottom-3 right-3 text-gray-500 hover:text-red-400 transition-colors text-sm p-1">
                    🗑️
                </button>
            </div>
        `).join(\'\');
    }

    document.getElementById(\'filter-date\').addEventListener(\'change\', applyFilters);
    document.getElementById(\'filter-type\').addEventListener(\'change\', applyFilters);

    async function archiveDashboard(filePath) {
        if (!confirm(`確定要備份移除 ${filePath}？\\n（檔案會移至 archive/ 資料夾，不會真正刪除）`)) return;
        try {
            const res = await fetch(`/api/dashboards/${filePath}`, { method: \'DELETE\' });
            const data = await res.json();
            if (data.success) {
                loadDashboards();
            } else {
                alert(\'移除失敗：\' + (data.detail || \'未知錯誤\'));
            }
        } catch (e) {
            alert(\'請求失敗：\' + e.message);
        }
    }

    // 初始載入
    loadDashboards();
    </script>
</body>
</html>'''


# ── main.py（統一入口：Web + Telegram + Scheduler 共用 asyncio event loop）──
MAIN_PY = '''"""ArkAgent OS 統一入口 — Web + Telegram + Scheduler 共用同一個 asyncio event loop"""
import os
import sys
import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# ── Logging 架構 ──
# 格式：時間 [層級] 來源 - 訊息
# 噪音來源統一壓到 WARNING，只留業務日誌

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    level=logging.INFO,
    stream=sys.stdout,
)

# 壓制噪音來源
for noisy in [
    "httpx",              # Telegram polling getUpdates / getMe
    "httpcore",           # httpx 底層連線
    "telegram.ext",       # python-telegram-bot 內部
    "google_genai",       # Gemini AFC enabled 等
    "uvicorn.access",     # uvicorn 每次 HTTP 請求
]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger("main")


# ── Web 伺服器（uvicorn 非阻塞模式） ──

async def start_web():
    """以 uvicorn.Server.serve() 協程啟動 FastAPI"""
    import uvicorn
    from entry.web_entry import app

    port = int(os.getenv("WEB_PORT", "2141"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    logger.info(f"[Web] 啟動中：http://localhost:{port}")
    await server.serve()


# ── Telegram Bot（手動控制 polling） ──

async def start_telegram():
    """以 Application.start() + updater.start_polling() 手動控制生命週期"""
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    from entry.telegram_entry import start, handle_message

    token = os.getenv("TELEGRAM_TOKEN", "")
    if not token:
        logger.warning("[Bot] TELEGRAM_TOKEN 未設定，跳過 Telegram Bot")
        return None

    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    builder = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
    )
    if proxy:
        builder = builder.proxy(proxy).get_updates_proxy(proxy)

    tg_app = builder.build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(bootstrap_retries=5)
    logger.info("[Bot] Telegram polling 已啟動")
    if proxy:
        logger.info(f"[Bot] proxy: {proxy}")
    return tg_app


# ── Scheduler（直接跑協程） ──

async def start_scheduler():
    """排程引擎 — 從 scheduler.py 匯入 main_loop"""
    try:
        from src.scheduler import main_loop
        logger.info("[Scheduler] 排程引擎啟動中")
        await main_loop()
    except asyncio.CancelledError:
        logger.info("[Scheduler] 排程引擎已停止")
    except Exception as e:
        logger.error(f"[Scheduler] 排程引擎異常：{e}")


# ── 主程式 ──

async def main():
    print("=" * 36)
    print("  ArkAgent OS Launcher (main.py)")
    print("=" * 36)

    # 1. 啟動 Telegram Bot（非阻塞）
    tg_app = await start_telegram()

    # 2. 啟動 Scheduler（背景 task）
    scheduler_task = asyncio.create_task(start_scheduler())

    # 3. 啟動 Web 伺服器（阻塞直到 shutdown）
    try:
        await start_web()
    except asyncio.CancelledError:
        pass
    finally:
        # Graceful shutdown
        logger.info("[Shutdown] 正在關閉服務...")
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

        if tg_app:
            await tg_app.updater.stop()
            await tg_app.stop()
            await tg_app.shutdown()
            logger.info("[Shutdown] Telegram Bot 已停止")

        logger.info("[Shutdown] 所有服務已關閉")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n[OK] 使用者中斷，服務已停止")
'''
