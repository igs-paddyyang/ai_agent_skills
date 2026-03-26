"""Tool Gateway 模板 — GATEWAY_PY, GEMINI_TOOL_PY, TELEGRAM_TOOL_PY, WEB_TOOL_PY, TOOLS_INIT_PY"""

# ── tools/gateway.py ──
GATEWAY_PY = '''"""Tool Gateway — 統一工具呼叫介面"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class BaseTool:
    """工具基底類別，所有工具必須實作此介面"""

    name: str = "base"
    description: str = ""

    async def call(self, **kwargs) -> Any:
        """執行工具，回傳結果"""
        raise NotImplementedError

    async def health_check(self) -> bool:
        """健康檢查，回傳是否可用"""
        return True


class ToolGateway:
    """
    統一工具管理與呼叫介面。
    所有外部工具（Gemini / Telegram / Web API）透過 Gateway 存取。
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        logger.info("ToolGateway 初始化完成")

    def register(self, tool: BaseTool):
        """註冊工具"""
        self._tools[tool.name] = tool
        logger.info(f"工具已註冊：{tool.name}")

    def unregister(self, name: str) -> bool:
        """取消註冊工具"""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"工具已取消註冊：{name}")
            return True
        return False

    async def call(self, name: str, **kwargs) -> Any:
        """呼叫指定工具"""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"工具 \\'{name}\\' 未註冊（可用：{list(self._tools.keys())}）")
        logger.debug(f"呼叫工具：{name}（params={list(kwargs.keys())}）")
        return await tool.call(**kwargs)

    def list_tools(self) -> list[dict]:
        """列出所有已註冊工具"""
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]

    async def health_check_all(self) -> dict[str, bool]:
        """檢查所有工具健康狀態"""
        results = {}
        for name, tool in self._tools.items():
            try:
                results[name] = await tool.health_check()
            except Exception:
                results[name] = False
        return results

    def get(self, name: str) -> BaseTool | None:
        """取得工具實例"""
        return self._tools.get(name)
'''

# ── tools/gemini_tool.py ──
GEMINI_TOOL_PY = '''"""Gemini API 工具 — LLM 呼叫封裝"""
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from tools.gateway import BaseTool
except ImportError:
    from gateway import BaseTool


class GeminiTool(BaseTool):
    """Gemini API 封裝，支援 generate_content"""

    name = "gemini"
    description = "Google Gemini API — 文字生成、意圖分類、摘要"

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def call(self, prompt: str = "", model: str = None, **kwargs) -> Any:
        """呼叫 Gemini API"""
        client = self._get_client()
        target_model = model or self.model
        try:
            response = client.models.generate_content(
                model=target_model, contents=prompt
            )
            return response.text if response.text else ""
        except Exception as e:
            logger.error(f"Gemini API 呼叫失敗：{e}")
            raise

    async def health_check(self) -> bool:
        """驗證 API Key 有效"""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            client.models.generate_content(
                model=self.model, contents="ping"
            )
            return True
        except Exception:
            return False
'''

# ── tools/telegram_tool.py ──
TELEGRAM_TOOL_PY = '''"""Telegram API 工具 — Bot 訊息發送封裝"""
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from tools.gateway import BaseTool
except ImportError:
    from gateway import BaseTool


class TelegramTool(BaseTool):
    """Telegram Bot API 封裝"""

    name = "telegram"
    description = "Telegram Bot API — 訊息發送與接收"

    def __init__(self, token: str = None):
        self.token = token or os.getenv("TELEGRAM_TOKEN", "")

    async def call(self, action: str = "send_message",
                   chat_id: str = "", text: str = "", **kwargs) -> Any:
        """執行 Telegram Bot API 操作"""
        import requests
        base_url = f"https://api.telegram.org/bot{self.token}"

        if action == "send_message":
            resp = requests.post(
                f"{base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            return resp.json()
        elif action == "get_me":
            resp = requests.get(f"{base_url}/getMe", timeout=10)
            return resp.json()
        else:
            raise ValueError(f"不支援的 action：{action}")

    async def health_check(self) -> bool:
        """驗證 Bot Token 有效"""
        if not self.token:
            return False
        try:
            result = await self.call(action="get_me")
            return result.get("ok", False)
        except Exception:
            return False
'''

# ── tools/web_tool.py ──
WEB_TOOL_PY = '''"""Web HTTP 工具 — 通用 HTTP 請求封裝"""
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

try:
    from tools.gateway import BaseTool
except ImportError:
    from gateway import BaseTool


class WebTool(BaseTool):
    """通用 HTTP 請求工具"""

    name = "web"
    description = "HTTP 請求工具 — GET / POST / 爬蟲"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; ArkAgent/1.0)"}

    async def call(self, url: str = "", method: str = "GET",
                   headers: dict = None, data: dict = None, **kwargs) -> Any:
        """執行 HTTP 請求"""
        req_headers = {**self.headers, **(headers or {})}
        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=req_headers, timeout=self.timeout)
            elif method.upper() == "POST":
                resp = requests.post(url, headers=req_headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"不支援的 method：{method}")
            resp.raise_for_status()
            return {"status": resp.status_code, "text": resp.text[:10000]}
        except requests.RequestException as e:
            logger.error(f"HTTP 請求失敗：{e}")
            raise

    async def health_check(self) -> bool:
        """檢查網路連線"""
        try:
            requests.get("https://httpbin.org/get", timeout=5)
            return True
        except Exception:
            return False
'''

# ── tools/__init__.py ──
TOOLS_INIT_PY = '''"""ArkAgent Tool Gateway — 統一工具管理"""
from .gateway import BaseTool, ToolGateway
from .gemini_tool import GeminiTool
from .telegram_tool import TelegramTool
from .web_tool import WebTool
'''
