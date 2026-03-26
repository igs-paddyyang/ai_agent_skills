"""核心層模板 — CORE_PY, CORE_LITE_PY, INTENT_ROUTER_PY, DASHBOARD_SKILL_PY, CRAWLER_SKILL_PY, FORMAT_UTILS_PY"""

# ── Lite 版 arkbot_core.py（不依賴 hybrid_router / controller / memory / planner）──
CORE_LITE_PY = '''"""ArkBot 核心邏輯（Lite 版）— Telegram 和 Web 共用

Lite 模式：Intent Router → Skill Registry → Executor
不含 Hybrid Router / Controller / Memory / Planner
"""
import json
import sys
import logging
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from intent_router import ArkBrain
from skill_registry import SkillRegistry
from executor import Executor

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

brain = ArkBrain()
_skill_dir = str(PROJECT_ROOT / "skills")
registry = SkillRegistry(_skill_dir)
executor = Executor(registry, _skill_dir)

logger.info(f"[ArkBot Lite] 載入 {len(registry.skills)} 個 Skill")


async def process_message(user_input: str) -> AsyncGenerator[dict, None]:
    """
    Lite 流程：
    1. Intent Router 分類意圖
    2. 依 intent 找 Skill → Executor 執行
    3. 無匹配 → CASUAL fallback（Gemini 閒聊）
    """
    yield {"type": "status", "content": "Thinking..."}

    # 意圖分類
    classify_result = brain.classify_intent(user_input)
    intent = classify_result.get("intent", "CASUAL")

    # 找匹配的 Skill
    matched = registry.filter_by_intent(intent)
    skill_id = matched[0]["skill_id"] if matched else None

    # tag 匹配（intent 沒命中時）
    if not skill_id:
        lower = user_input.lower()
        for sid, meta in registry.skills.items():
            tags = [t.lower() for t in meta.get("tags", [])]
            if any(t in lower for t in tags):
                skill_id = sid
                intent = meta.get("intent", "UNKNOWN")
                break

    logger.info(f"路由結果：intent={intent}, skill_id={skill_id}")

    # CASUAL 快速路徑
    if intent == "CASUAL" and not skill_id:
        reply = brain.chat(user_input)
        yield {"type": "reply", "content": reply}
        return

    # 有 Skill → 執行
    if skill_id:
        yield {"type": "status", "content": f"Executing {skill_id}..."}
        result = await executor.execute(skill_id, user_input)
        if result.get("success"):
            meta = registry.get_skill(skill_id)
            response_type = meta.get("response_type", "text") if meta else "text"
            raw = result.get("result", "")

            if response_type == "dashboard" and isinstance(raw, dict) and "html_path" in raw:
                yield {"type": "dashboard", "content": raw.get("summary", ""), "html_path": raw["html_path"]}
            else:
                yield {"type": "reply", "content": str(raw)}
        else:
            logger.warning(f"Skill \\'{skill_id}\\' failed, fallback: {result.get('error')}")
            reply = brain.chat(user_input)
            yield {"type": "reply", "content": reply}
        return

    # 無匹配 → CASUAL
    reply = brain.chat(user_input)
    yield {"type": "reply", "content": reply}
'''

# arkbot_core.py 模板（整合 Hybrid Router + Executor + DomainController + Memory + Planner）
CORE_PY = '''"""ArkBot 核心邏輯 — Telegram 和 Web 共用（整合 Hybrid Router + Executor + DomainController + Memory + Planner）"""
import json
import sys
import logging
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 讓 controller/, memory/, planner/ 可被 import（Issue #7）
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from intent_router import ArkBrain
from hybrid_router import route, registry
from executor import Executor

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

brain = ArkBrain()
_skill_dir = str(PROJECT_ROOT / "skills")
executor = Executor(registry, _skill_dir)

# ── DomainController 初始化 ──
_domain_controller = None
try:
    from controller.domain_controller import DomainController
    _domain_controller = DomainController(str(PROJECT_ROOT), registry)
    executor.set_domain_controller(_domain_controller)
    logger.info("DomainController 已載入")
except ImportError:
    logger.info("DomainController 未安裝，Action 路由功能停用")

# ── Memory 初始化 ──
_memory = None
try:
    from memory.short_term import ShortTermMemory
    _memory = ShortTermMemory(max_turns=10)
    logger.info("ShortTermMemory 已載入")
except ImportError:
    logger.info("Memory 模組未安裝，對話記憶功能停用")

# ── Planner 初始化 ──
_planner = None
try:
    from planner.planner import SkillPlanner
    _planner = SkillPlanner()
    logger.info("SkillPlanner 已載入")
except ImportError:
    logger.info("Planner 模組未安裝，多步驟規劃功能停用")


def _get_context() -> str:
    """取得最近對話 context（供 Intent / Planner 使用）"""
    if not _memory:
        return ""
    return _memory.get_context_string(last_n=5)


async def process_message(user_input: str) -> AsyncGenerator[dict, None]:
    """
    流程：
    1. Hybrid Router 路由（注入對話 context）
    2. CASUAL → brain.chat 直接回覆
    3. Planner 判斷是否需要多步驟
    4. 有 Skill → Executor 執行（根據 response_type 決定 yield 類型）
    5. Action 偵測 → DomainController 執行
    6. Memory 記錄對話
    """
    yield {"type": "status", "content": "🧠 正在思考..."}

    context = _get_context()

    # Hybrid Router 路由
    route_result = await route(user_input)
    intent = route_result["intent"]
    skill_id = route_result.get("skill_id")
    method = route_result.get("method")

    logger.info(
        f"路由結果：intent={intent}, skill_id={skill_id}, "
        f"method={method}, reason={route_result.get('reason')}"
    )

    reply = ""

    # ── CASUAL 快速路徑 ──
    if intent == "CASUAL":
        reply = brain.chat(user_input + ("\\n\\n對話紀錄：\\n" + context if context else ""))
        yield {"type": "reply", "content": reply}
        if _memory:
            _memory.add("user", user_input)
            _memory.add("assistant", reply)
        return

    # ── Planner：判斷是否需要多步驟 ──
    # DASHBOARD intent 跳過 Planner（單一 Skill，不需多步驟分析）
    if _planner and skill_id and intent not in ("DASHBOARD", "DASHBOARD_CANVAS"):
        yield {"type": "status", "content": "📋 規劃執行步驟..."}
        plan = await _planner.analyze(user_input, registry.skills, context)

        if not plan.is_simple and len(plan.steps) > 1:
            # 多步驟執行
            yield {"type": "status", "content": f"⚙️ 執行 {len(plan.steps)} 個步驟..."}
            results = await executor.execute_plan(plan)
            # 彙整結果
            summaries = []
            for i, r in enumerate(results, 1):
                if r.get("success"):
                    text = r.get("fallback_text") or str(r.get("result", ""))[:200]
                    summaries.append(f"步驟 {i} ✅ {text}")
                else:
                    summaries.append(f"步驟 {i} ❌ {r.get('error', '未知錯誤')}")
            reply = "\\n".join(summaries)
            yield {"type": "reply", "content": reply}
            if _memory:
                _memory.add("user", user_input)
                _memory.add("assistant", reply)
            return

    # ── 有匹配 Skill → Executor 執行 ──
    if skill_id:
        yield {"type": "status", "content": f"⚙️ 執行 Skill：{skill_id}..."}
        result = await executor.execute(skill_id, user_input)
        if result.get("success"):
            # 根據 skill metadata 的 response_type 決定 yield 類型
            meta = registry.get_skill(skill_id)
            response_type = meta.get("response_type", "text") if meta else "text"
            raw = result.get("result", "")

            # Action 執行結果可能有 fallback_text
            if result.get("fallback_text"):
                reply = result["fallback_text"]
                yield {"type": "reply", "content": reply}
            elif response_type == "dashboard":
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        pass
                if isinstance(raw, dict) and "html_path" in raw:
                    reply = raw.get("summary", "")
                    yield {
                        "type": "dashboard",
                        "content": reply,
                        "html_path": raw["html_path"],
                    }
                else:
                    reply = str(raw)
                    yield {"type": "reply", "content": reply}
            else:
                reply = str(raw)
                yield {"type": "reply", "content": reply}
        else:
            logger.warning(f"Skill \\'{skill_id}\\' 執行失敗，fallback 到 CASUAL：{result.get('error')}")
            reply = brain.chat(user_input)
            yield {"type": "reply", "content": reply}

        if _memory:
            _memory.add("user", user_input)
            _memory.add("assistant", reply)
        return

    # ── 無匹配 Skill → CASUAL fallback ──
    reply = brain.chat(user_input)
    yield {"type": "reply", "content": reply}
    if _memory:
        _memory.add("user", user_input)
        _memory.add("assistant", reply)
'''


# intent_router.py 模板（含意圖分類、日期提取、關鍵字快速匹配、Spec 驅動動態意圖）
INTENT_ROUTER_PY = '''"""ArkBrain — 意圖分類、摘要與閒聊（四個方法、四個獨立 prompt，絕不混用）

支援 Spec 驅動動態意圖：從 agent.yaml 讀取 intents 清單，LLM 分類 prompt 動態生成。
無 agent.yaml 時 fallback 到預設 3 種意圖（RESEARCH / DASHBOARD / CASUAL）。
"""
import json
import re
import os
import logging
from datetime import datetime
from pathlib import Path
from google import genai
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

logger = logging.getLogger(__name__)

# URL 偵測正則
URL_PATTERN = re.compile(r'https?://[^\\s<>"{}|\\\\^`\\[\\]]+')

# 日期提取正則
DATE_PATTERNS = [
    re.compile(r'(\\d{4})[/\\-](\\d{1,2})[/\\-](\\d{1,2})'),
    re.compile(r'(\\d{8})'),
    re.compile(r'(\\d{1,2})[/\\-](\\d{1,2})'),
    re.compile(r'(\\d{1,2})月(\\d{1,2})[日號]?'),
]

# 預設意圖（無 agent.yaml 時使用）
DEFAULT_INTENTS = {
    "RESEARCH": "包含網址、詢問知識、技術問題",
    "DASHBOARD": "提到儀表板、dashboard、產生圖表",
    "DASHBOARD_CANVAS": "明確要求用 AI/Gemini/Canvas 自由排版儀表板",
    "SQL_QUERY": "查詢資料庫、SQL、查資料、SELECT",
    "BIGQUERY": "BigQuery、BQ、大數據查詢",
    "KPI_ANALYSIS": "分析 KPI 數據、指標分析",
    "ANOMALY_DETECT": "異常偵測、數據波動、RTP 異常",
    "MSSQL_QUERY": "MSSQL、SQL Server、mssql 查詢",
    "CASUAL": "閒聊、打招呼、情緒表達",
}


def _load_intents_from_yaml() -> dict[str, str]:
    """從 agent.yaml 讀取意圖清單，回傳 {intent_name: description}"""
    yaml_paths = [
        PROJECT_ROOT / "agents" / "default" / "agent.yaml",
        PROJECT_ROOT / "specs" / "examples" / "agent-example.yaml",
    ]
    for yaml_path in yaml_paths:
        if yaml_path.exists():
            try:
                import yaml
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                intents = data.get("intents", {})
                if intents:
                    # 支援兩種格式：list ["RESEARCH", "CASUAL"] 或 dict {"RESEARCH": "描述"}
                    if isinstance(intents, list):
                        result = {}
                        for item in intents:
                            if isinstance(item, str):
                                result[item] = DEFAULT_INTENTS.get(item, item)
                            elif isinstance(item, dict):
                                result.update(item)
                        intents = result
                    logger.info(f"從 {yaml_path.name} 載入 {len(intents)} 個意圖")
                    return intents
            except ImportError:
                # 無 yaml 套件，嘗試簡易解析
                pass
            except Exception as e:
                logger.warning(f"agent.yaml 解析失敗: {e}")
    return DEFAULT_INTENTS


def extract_date(text: str):
    """從文字中提取日期，回傳 YYYYMMDD 整數或 None"""
    now = datetime.now()
    for i, pat in enumerate(DATE_PATTERNS):
        m = pat.search(text)
        if not m:
            continue
        if i == 0:
            return int(f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}")
        elif i == 1:
            return int(m.group(1))
        elif i == 2:
            return int(f"{now.year}{int(m.group(1)):02d}{int(m.group(2)):02d}")
        elif i == 3:
            return int(f"{now.year}{int(m.group(1)):02d}{int(m.group(2)):02d}")
    return None


class ArkBrain:
    """四個方法、四個獨立 prompt，絕不混用。支援動態意圖。"""

    def __init__(self):
        self._intents = _load_intents_from_yaml()

    def reload_intents(self):
        """重新載入意圖清單（agent.yaml 變更後呼叫）"""
        self._intents = _load_intents_from_yaml()

    def _build_intent_prompt(self, user_input: str, context: str = "") -> str:
        """動態生成意圖分類 prompt"""
        intent_rules = "\\n".join(
            f"- {name}：{desc}" for name, desc in self._intents.items()
        )
        intent_names = "|".join(f\'\\"{name}\\"\' for name in self._intents)

        context_section = ""
        if context:
            context_section = f"\\n對話紀錄（參考用）：\\n{context}\\n"

        return f"""你是一個數據分流器。根據使用者輸入，判斷意圖類型。
只回傳 JSON，不要其他文字。

規則：
- 包含網址 → RESEARCH
{intent_rules}
{context_section}
使用者輸入：{user_input}

回傳格式：{{"intent": {intent_names}, "url": null}}"""

    def classify_intent(self, user_input: str, context: str = "") -> dict:
        """意圖分類，回傳 JSON。先用規則快速匹配，再走 Gemini。"""
        lower = user_input.lower()

        # ANOMALY_DETECT 關鍵字快速路徑
        anomaly_keywords = ["異常偵測", "異常分析", "數據波動", "rtp異常", "anomaly"]
        if any(kw in lower for kw in anomaly_keywords):
            return {"intent": "ANOMALY_DETECT", "url": None}

        # BIGQUERY 關鍵字快速路徑
        bq_keywords = ["bigquery", "bq查詢", "bq ", "大數據查詢"]
        if any(kw in lower for kw in bq_keywords):
            return {"intent": "BIGQUERY", "url": None}

        # SQL_QUERY 關鍵字快速路徑
        sql_keywords = ["select ", "查詢資料庫", "查資料庫", "sql查詢", "sql "]
        if any(kw in lower for kw in sql_keywords):
            return {"intent": "SQL_QUERY", "url": None}

        # MSSQL_QUERY 關鍵字快速路徑
        mssql_keywords = ["mssql", "sql server", "sqlserver"]
        if any(kw in lower for kw in mssql_keywords):
            return {"intent": "MSSQL_QUERY", "url": None}

        # DASHBOARD_CANVAS 關鍵字快速路徑（canvas / gemini 畫 / AI 畫）
        canvas_keywords = ["canvas", "gemini畫", "ai畫", "gemini dashboard", "自由排版"]
        if any(kw in lower for kw in canvas_keywords):
            return {"intent": "DASHBOARD_CANVAS", "url": None}

        # DASHBOARD 關鍵字快速路徑（優先於 URL 偵測，避免含路徑的輸入被誤判為 RESEARCH）
        dashboard_keywords = ["儀表板", "dashboard", "營收分析", "老虎機分析", "魚機分析", "產生圖表"]
        if any(kw in lower for kw in dashboard_keywords):
            return {"intent": "DASHBOARD", "url": None}

        # URL 偵測
        urls = URL_PATTERN.findall(user_input)
        if urls:
            return {"intent": "RESEARCH", "url": urls[0]}

        prompt = self._build_intent_prompt(user_input, context)

        resp = client.models.generate_content(model=MODEL, contents=prompt)
        try:
            text = resp.text.strip()
            if text.startswith("```"):
                text = re.sub(r\'^```\\w*\\n?\', \'\', text)
                text = re.sub(r\'\\n?```$\', \'\', text)
            result = json.loads(text)
            # 驗證意圖是否在清單中
            if result.get("intent") not in self._intents:
                result["intent"] = "CASUAL"
            return result
        except (json.JSONDecodeError, AttributeError):
            return {"intent": "CASUAL", "url": None}

    def summarize_content(self, markdown_content: str, user_input: str = "") -> str:
        """研究型摘要，含腳註標註來源。僅用於研究型內容。"""
        prompt = f"""你是資深研究分析師。請根據以下 Markdown 內容產出繁體中文結構化摘要。
使用腳註標註資訊來源。格式：重點摘要 + 關鍵發現 + 行動建議。

使用者問題：{user_input}

內容：
{markdown_content[:8000]}"""
        resp = client.models.generate_content(model=MODEL, contents=prompt)
        return resp.text if resp.text else "⚠️ 摘要產生失敗"

    def chat(self, user_input: str) -> str:
        """閒聊型對話，友善直接回應。絕不使用摘要格式。"""
        prompt = f"""你是一個友善的助理。直接用自然對話回應使用者，
語氣輕鬆親切，使用繁體中文。不要用條列式或摘要格式。

使用者：{user_input}"""
        resp = client.models.generate_content(model=MODEL, contents=prompt)
        return resp.text if resp.text else "嗨！有什麼我可以幫忙的嗎？"
'''


# crawler_skill.py 模板（從 generate() 內嵌提取）
CRAWLER_SKILL_PY = '''"""Ark 爬蟲引擎 — 快取優先策略"""
import sqlite3
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

_db_rel = os.getenv("DATABASE_PATH", "data/brain.db")
DB_PATH = str(PROJECT_ROOT / _db_rel) if not os.path.isabs(_db_rel) else _db_rel
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArkBot/1.0)"}
TIMEOUT = 15


def get_cached(url: str) -> str | None:
    """查詢快取，有資料就直接回傳。"""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT content_md FROM raw_crawls WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row[0] if row else None


def crawl_and_store(url: str) -> str:
    """爬取網頁並存入資料庫，回傳 Markdown 內容。"""
    # 快取優先
    cached = get_cached(url)
    if cached:
        return cached

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"[ERROR] 無法獵取：{e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    # 移除 script/style 標籤
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    content_md = md(str(soup.body or soup), heading_style="ATX")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO raw_crawls (url, content_md) VALUES (?, ?)",
            (url, content_md),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # UNIQUE 約束，已存在就跳過
    finally:
        conn.close()

    return content_md
'''


# format_utils.py 模板（從 generate() 內嵌提取）
FORMAT_UTILS_PY = r'''"""MarkdownV2 跳脫工具"""
import re

# MarkdownV2 保留字元完整清單
_MARKDOWN_V2_SPECIAL = r'\_*[]()~`>#+-=|{}.!'

def escape_markdown_v2(text: str) -> str:
    """跳脫 MarkdownV2 保留字元，用於動態內容。
    靜態字串請手動跳脫，不要用此函式。"""
    return re.sub(r'([' + re.escape(_MARKDOWN_V2_SPECIAL) + r'])', r'\\\1', text)
'''


# gemini_canvas_skill.py 模板（Gemini Canvas 自由排版模式）
GEMINI_CANVAS_SKILL_PY = '''"""儀表板產生器（Gemini Canvas）— 讀取 JSON → 呼叫 Gemini API → 產出 HTML 儀表板"""
import json
import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

DASHBOARD_DIR = PROJECT_ROOT / "data" / "dashboard"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

# 延遲初始化 Gemini client
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _client


# ── Prompt 模板 ──────────────────────────────────────────────

PROMPT_TEMPLATE = """Role: Senior Frontend & Data Visualization Expert specializing in premium SaaS dashboards.
Task: Create a professional, premium-looking single-file Dashboard HTML based on the provided data.

=== TECHNICAL STACK (MANDATORY) ===
- Google Fonts: Inter (weights: 300, 400, 500, 600, 700)
- CSS: Tailwind CSS (via CDN: https://cdn.tailwindcss.com)
- JS: Chart.js 4.x (via CDN: https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js)

=== DESIGN SYSTEM ===
Theme: Light mode, clean and airy.
Background: #f8fafc | Cards: Glass-morphism (rgba(255,255,255,0.95), backdrop-filter blur(10px))
Colors: Primary #2563eb, Success #10b981, Warning #f59e0b, Danger #ef4444, Purple #8b5cf6
Chart palette: [\'#2563eb\',\'#10b981\',\'#f59e0b\',\'#ef4444\',\'#8b5cf6\',\'#6b7280\',\'#ec4899\',\'#14b8a6\']
Font: \'Inter\', sans-serif | Title: text-3xl font-bold | Body: text-sm text-slate-600

=== LAYOUT RULES ===
1. KPI Cards: grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4, each with title + value + trend badge
2. Charts: Line for trends, Doughnut for distribution, Bar for comparison
3. Tables: glass-card wrapper, overflow-x-auto, alternating rows
4. Footer: "© 2026 paddyyang | AIBI 數據中心"
5. Use Chinese (繁體中文) for ALL UI labels

=== CRITICAL REQUIREMENTS ===
1. Output a single, complete, self-contained HTML file
2. ALL data embedded as JavaScript const variable named `DATA`
3. ALL charts and KPI cards MUST read from the `DATA` variable — never hardcode values
4. No fetch() or external API calls — must work offline (except CDN)
5. HTML must start with <!DOCTYPE html> and end with </html>
6. Include CSS fallback for file:// offline support
7. Add fadeIn animation with staggered delay
8. Verify every chart dataset references `DATA.trend`, `DATA.top_games`, `DATA.distribution` etc.

=== DASHBOARD INFO ===
Dashboard Title: {title}

=== DATA TO VISUALIZE ===
```json
{data}
```

Analyze the data structure and create the most appropriate premium-quality visualizations.
Generate the complete HTML now."""


# ── 工具函式 ─────────────────────────────────────────────────

def extract_html(text: str) -> str:
    """從 Gemini 回應中提取 HTML"""
    match = re.search(r\'```html\\s*\\n(.*?)```\', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r\'(<!DOCTYPE html>.*?</html>)\', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_json_path(user_input: str) -> str | None:
    """從使用者輸入中提取 JSON 檔案路徑"""
    match = re.search(r\'((?:data/)?dashboard/\\S+\\.json|[\\w./\\\\-]+\\.json)\', user_input)
    if match:
        path = match.group(1)
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            return str(full_path)
    return None


def parse_date(user_input: str) -> str:
    """從使用者輸入提取日期，預設昨日"""
    patterns = [
        (re.compile(r\'(\\d{4})[/\\-](\\d{1,2})[/\\-](\\d{1,2})\'), lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"),
        (re.compile(r\'(\\d{1,2})[/\\-](\\d{1,2})\'), lambda m: f"{datetime.now().year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
        (re.compile(r\'(\\d{1,2})月(\\d{1,2})[日號]?\'), lambda m: f"{datetime.now().year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
    ]
    for pat, fmt in patterns:
        m = pat.search(user_input)
        if m:
            return fmt(m)
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def detect_dashboard_type(user_input: str) -> str:
    """偵測儀表板類型：revenue / slots / fish / general"""
    lower = user_input.lower()
    if any(kw in lower for kw in ["營收", "revenue", "玩家", "儲值", "arpu", "ggr"]):
        return "revenue"
    if any(kw in lower for kw in ["老虎機", "slots", "slot", "每轉", "spin"]):
        return "slots"
    if any(kw in lower for kw in ["魚機", "fish", "捕魚", "tigershark", "shark"]):
        return "fish"
    return "general"


def get_sample_json(dashboard_type: str) -> str | None:
    """取得對應類型最新的 JSON 路徑（從 data/dashboard/{type}/ 目錄）"""
    if dashboard_type == "general":
        return None
    type_dir = DASHBOARD_DIR / dashboard_type
    if not type_dir.exists():
        return None
    # 找最新的 .json（按檔名排序，日期格式 YYYY-MM-DD.json）
    jsons = sorted(type_dir.glob("*.json"), reverse=True)
    if jsons:
        return str(jsons[0])
    return None


# ── 核心流程 ─────────────────────────────────────────────────

TITLE_MAP = {
    "revenue": "營收分析儀表板",
    "slots": "老虎機分析儀表板",
    "fish": "魚機分析儀表板",
    "general": "數據儀表板",
}


async def generate_dashboard(json_path: str, title: str = None) -> dict:
    """
    核心函式：讀取 JSON → 呼叫 Gemini API → 產出 HTML → 存檔。
    回傳 {"html_path": str, "summary": str}
    """
    path = Path(json_path)
    if not path.exists():
        return {"error": f"找不到 JSON 檔案：{json_path}"}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not title:
        title = data.get("title", "Data Dashboard")

    data_str = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.replace("{title}", title).replace("{data}", data_str)

    logger.info(f"呼叫 Gemini API 產生儀表板：{title}")
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )
    except Exception as e:
        logger.error(f"Gemini API 呼叫失敗：{e}")
        return {"error": f"Gemini API 呼叫失敗：{e}"}

    if not response.text:
        return {"error": "Gemini API 回應為空"}

    html = extract_html(response.text)

    # 存檔 — 依類型存到子目錄 data/dashboard/{type}/
    dtype = _detect_type_from_data(data)
    type_dir = DASHBOARD_DIR / dtype
    type_dir.mkdir(parents=True, exist_ok=True)
    date_str = data.get(\'date\', datetime.now().strftime("%Y-%m-%d"))
    ts = datetime.now().strftime("%H%M%S")
    filename = f"{date_str}_{ts}.html"
    output_path = type_dir / filename
    output_path.write_text(html, encoding="utf-8")
    logger.info(f"儀表板已存檔：{output_path}")

    rel_path = f"{dtype}/{filename}"
    summary = f"📊 {title}\\n📅 資料日期：{data.get(\'date\', \'N/A\')}\\n📁 檔案：{rel_path}"
    return {"html_path": str(output_path), "summary": summary}


async def generate_dashboard_from_input(user_input: str) -> dict:
    """
    協調器：解析使用者輸入 → 決定 JSON 來源 → 呼叫 generate_dashboard。
    回傳 {"html_path": str, "summary": str} 或 {"error": str}
    """
    # 1. 嘗試從輸入提取 JSON 路徑
    json_path = parse_json_path(user_input)

    # 2. 若無明確路徑，依類型使用範例 JSON
    dashboard_type = detect_dashboard_type(user_input)
    if not json_path:
        json_path = get_sample_json(dashboard_type)

    if not json_path:
        return {"error": "找不到可用的 JSON 資料。請指定 JSON 檔案路徑，或確認 data/dashboard/ 下有範例檔案。"}

    # 3. 決定標題
    title = TITLE_MAP.get(dashboard_type)

    return await generate_dashboard(json_path, title)


def _detect_type_from_data(data: dict) -> str:
    """從 JSON 資料內容偵測類型"""
    title = data.get("title", "").lower()
    source = data.get("source", "").lower()
    if "slot" in title or "老虎機" in data.get("title", "") or "老虎机" in data.get("title", ""):
        return "slots"
    if "fish" in title or "魚機" in data.get("title", "") or "鱼机" in data.get("title", "") or "shark" in source:
        return "fish"
    if "revenue" in title or "營收" in data.get("title", "") or "营收" in data.get("title", ""):
        return "revenue"
    return "general"


def _apply_date_to_json(json_path: str, target_date: str) -> str:
    """若 JSON 中的 date 與目標日期不同，建立臨時副本並替換日期"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("date") == target_date:
        return json_path

    data["date"] = target_date
    # 寫入臨時檔案
    tmp_path = DASHBOARD_DIR / f"_tmp_{Path(json_path).name}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(tmp_path)
'''


# dashboard_skill.py 模板（三層架構：JSON → DSL → Renderer → HTML）
DASHBOARD_SKILL_PY = '''"""儀表板產生器（三層架構）— JSON → DSL → Renderer → HTML

使用內嵌 dashboard_engine 引擎，取代 LLM 直出 HTML。
DSL 模式：純程式碼渲染，穩定可控。
Auto 模式：Gemini API 產 DSL → 程式碼渲染 HTML。
"""
import json
import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

DASHBOARD_DIR = PROJECT_ROOT / "data" / "dashboard"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

# ── 載入內嵌 dashboard engine ──
from dashboard_engine import generate_dashboard as _engine_generate
from dashboard_engine import validate_data, detect_data_type, build_fallback_dsl


# ── 工具函式 ──────────────────────────────────────

def parse_json_path(user_input: str) -> str | None:
    """從使用者輸入中提取 JSON 檔案路徑"""
    match = re.search(r\'((?:data/)?dashboard/\\S+\\.json|[\\w./\\\\-]+\\.json)\', user_input)
    if match:
        path = match.group(1)
        full_path = PROJECT_ROOT / path
        if full_path.exists():
            return str(full_path)
    return None


def parse_date(user_input: str) -> str:
    """從使用者輸入提取日期，預設昨日"""
    patterns = [
        (re.compile(r\'(\\d{4})[/\\-](\\d{1,2})[/\\-](\\d{1,2})\'), lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"),
        (re.compile(r\'(\\d{1,2})[/\\-](\\d{1,2})\'), lambda m: f"{datetime.now().year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
        (re.compile(r\'(\\d{1,2})月(\\d{1,2})[日號]?\'), lambda m: f"{datetime.now().year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
    ]
    for pat, fmt in patterns:
        m = pat.search(user_input)
        if m:
            return fmt(m)
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def detect_dashboard_type(user_input: str) -> str:
    """偵測儀表板類型：revenue / slots / fish / general"""
    lower = user_input.lower()
    if any(kw in lower for kw in ["營收", "revenue", "玩家", "儲值", "arpu", "ggr"]):
        return "revenue"
    if any(kw in lower for kw in ["老虎機", "slots", "slot", "每轉", "spin"]):
        return "slots"
    if any(kw in lower for kw in ["魚機", "fish", "捕魚", "tigershark", "shark"]):
        return "fish"
    return "general"


def get_sample_json(dashboard_type: str) -> str | None:
    """取得對應類型最新的 JSON 路徑"""
    if dashboard_type == "general":
        return None
    type_dir = DASHBOARD_DIR / dashboard_type
    if not type_dir.exists():
        return None
    jsons = sorted(type_dir.glob("*.json"), reverse=True)
    if jsons:
        return str(jsons[0])
    return None


TITLE_MAP = {
    "revenue": "營收分析儀表板",
    "slots": "老虎機分析儀表板",
    "fish": "魚機分析儀表板",
    "general": "數據儀表板",
}


# ── 核心流程 ─────────────────────────────────────────────────

async def generate_dashboard(json_path: str, title: str = None, mode: str = "auto") -> dict:
    """
    核心函式：讀取 JSON → DSL → Renderer → HTML → 存檔。
    回傳 {"html_path": str, "summary": str} 或 {"error": str}
    """
    path = Path(json_path)
    if not path.exists():
        return {"error": f"找不到 JSON 檔案：{json_path}"}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not title:
        title = data.get("title", "Data Dashboard")

    # 呼叫三層架構引擎（內嵌版）
    logger.info(f"呼叫 Dashboard Engine（{mode} 模式）：{title}")
    result = _engine_generate(
        data=data,
        mode=mode,
        title=title,
        output_dir=DASHBOARD_DIR,
    )

    if "error" in result:
        return {"error": result["error"]}

    # 組裝回傳
    html_path = result["html_path"]
    meta = result.get("metadata", {})
    date_str = data.get("date", "N/A")
    rel_path = str(Path(html_path).relative_to(PROJECT_ROOT))

    summary = (
        f"📊 {title}\\n"
        f"📅 資料日期：{date_str}\\n"
        f"📁 檔案：{rel_path}\\n"
        f"📈 widgets={meta.get(\'widgets\', 0)}, "
        f"charts={meta.get(\'charts\', 0)}, "
        f"tables={meta.get(\'tables\', 0)}, "
        f"kpi={meta.get(\'kpi_cards\', 0)}"
    )

    return {"html_path": html_path, "summary": summary}


async def generate_dashboard_from_input(user_input: str) -> dict:
    """
    協調器：解析使用者輸入 → 決定 JSON 來源 → 呼叫 generate_dashboard。
    回傳 {"html_path": str, "summary": str} 或 {"error": str}
    """
    # 1. 嘗試從輸入提取 JSON 路徑
    json_path = parse_json_path(user_input)

    # 2. 若無明確路徑，依類型使用範例 JSON
    dashboard_type = detect_dashboard_type(user_input)
    if not json_path:
        json_path = get_sample_json(dashboard_type)

    if not json_path:
        return {"error": "找不到可用的 JSON 資料。請指定 JSON 檔案路徑，或確認 data/dashboard/ 下有範例檔案。"}

    # 3. 決定標題與模式
    title = TITLE_MAP.get(dashboard_type)

    # 判斷模式：有 GOOGLE_API_KEY 時用 auto（AI 產 DSL），否則用 fallback
    mode = "auto" if os.getenv("GOOGLE_API_KEY") else "dsl"

    return await generate_dashboard(json_path, title, mode)
'''
