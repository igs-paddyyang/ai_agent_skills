"""API Gateway 模板 — app.py / auth.py / rate_limiter.py / websocket_handler.py"""

# ── gateway/__init__.py ──
GATEWAY_INIT_PY = '''"""ArkAgent API Gateway — 認證 + 限流 + 路由"""
from .app import create_app

__all__ = ["create_app"]
'''

# ── gateway/auth.py ──
GATEWAY_AUTH_PY = '''"""認證中介層 — API Key / Bearer Token 驗證"""
import os
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 不需認證的路徑
PUBLIC_PATHS = {"/", "/health", "/ws/chat"}


class AuthMiddleware(BaseHTTPMiddleware):
    """API Key 認證中介層"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 公開路徑 + WebSocket 不需認證
        if path in PUBLIC_PATHS or path.startswith("/ws/"):
            return await call_next(request)

        # 靜態資源不需認證
        if path.startswith("/static/") or path == "/dashboard":
            return await call_next(request)

        # 驗證 API Key
        api_key = os.getenv("SKILL_API_KEY", "")
        if not api_key:
            # 未設定 API Key 時，所有 /api/ 路徑都拒絕
            if path.startswith("/api/"):
                raise HTTPException(status_code=500, detail="SKILL_API_KEY 未設定")
            return await call_next(request)

        # 從 Header 或 Query 取得 Key
        provided_key = (
            request.headers.get("x-api-key")
            or request.headers.get("authorization", "").removeprefix("Bearer ")
            or request.query_params.get("api_key")
        )

        if path.startswith("/api/") and provided_key != api_key:
            logger.warning(f"認證失敗: {request.client.host} → {path}")
            raise HTTPException(status_code=401, detail="無效的 API Key")

        return await call_next(request)
'''

# ── gateway/rate_limiter.py ──
GATEWAY_RATE_LIMITER_PY = '''"""限流中介層 — In-memory Sliding Window"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 預設限流：每分鐘 60 次
DEFAULT_RATE_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding Window 限流"""

    def __init__(self, app, rate_limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_WINDOW_SECONDS):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """取得客戶端識別（IP + API Key）"""
        api_key = request.headers.get("x-api-key", "")
        client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{api_key}" if api_key else client_ip

    def _cleanup(self, client_id: str, now: float):
        """清理過期的請求記錄"""
        cutoff = now - self.window
        self._requests[client_id] = [t for t in self._requests[client_id] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # 只對 /api/ 路徑限流
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()
        self._cleanup(client_id, now)

        if len(self._requests[client_id]) >= self.rate_limit:
            logger.warning(f"限流觸發: {client_id} ({len(self._requests[client_id])}/{self.rate_limit})")
            raise HTTPException(
                status_code=429,
                detail=f"請求過於頻繁，每 {self.window} 秒最多 {self.rate_limit} 次",
            )

        self._requests[client_id].append(now)
        return await call_next(request)
'''


# ── gateway/websocket_handler.py ──
GATEWAY_WEBSOCKET_PY = '''"""WebSocket 對話處理器"""
import json
import os
import logging
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """封裝 WebSocket 對話邏輯"""

    def __init__(self, process_message_fn):
        """
        Args:
            process_message_fn: async generator，接收 user_input，yield event dict
        """
        self.process_message = process_message_fn

    async def handle(self, ws: WebSocket):
        """處理單一 WebSocket 連線"""
        await ws.accept()
        logger.info(f"WebSocket 連線已建立: {ws.client}")

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
                    async for event in self.process_message(user_input):
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
                    logger.error(f"處理失敗: {e}")
                    await ws.send_json({"type": "error", "content": f"處理失敗: {str(e)}"})

        except WebSocketDisconnect:
            logger.info("WebSocket 連線已斷開")
        except Exception as e:
            logger.error(f"WebSocket 錯誤: {e}")
            try:
                await ws.send_json({"type": "error", "content": f"伺服器錯誤: {str(e)}"})
            except Exception:
                pass
'''

# ── gateway/app.py ──
GATEWAY_APP_PY = '''"""API Gateway 主應用 — FastAPI + 認證 + 限流 + 路由"""
import os
import glob
import json
import time
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from .auth import AuthMiddleware
from .rate_limiter import RateLimiterMiddleware
from .websocket_handler import WebSocketHandler

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class SkillRequest(BaseModel):
    """Skill API 請求格式"""
    input: str
    params: dict = {}


def create_app() -> FastAPI:
    """建立 Gateway FastAPI 應用"""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "__COMPAT_DIR__"))

    from arkbot_core import process_message
    from runtime.registry import SkillRegistry
    from runtime.executor import Executor

    app = FastAPI(title="ArkAgent Gateway", version="2.0")

    # 中介層（順序：限流 → 認證）
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimiterMiddleware)

    WEB_DIR = PROJECT_ROOT / "web"
    DASHBOARD_DIR = PROJECT_ROOT / "data" / "dashboard"
    _skill_dir = str(PROJECT_ROOT / "skills")
    _registry = SkillRegistry(_skill_dir)
    _executor = Executor(_registry, _skill_dir)
    _ws_handler = WebSocketHandler(process_message)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html_path = WEB_DIR / "index.html"
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")
        return HTMLResponse("<h1>ArkAgent</h1><p>Web UI 未找到</p>")

    @app.get("/health")
    async def health():
        return {"status": "ok", "skills": len(_registry.skills)}

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_view(file: str = Query(default=None)):
        if file:
            html_path = DASHBOARD_DIR / file
        else:
            pattern = str(DASHBOARD_DIR / "dashboard_*.html")
            files = sorted(glob.glob(pattern), reverse=True)
            html_path = Path(files[0]) if files else None
        if html_path and html_path.exists():
            return html_path.read_text(encoding="utf-8")
        return HTMLResponse("<h1>尚未產生儀表板</h1>", status_code=404)

    @app.websocket("/ws/chat")
    async def websocket_chat(ws: WebSocket):
        await _ws_handler.handle(ws)

    @app.get("/api/skills")
    async def list_skills():
        skills = [
            {"skill_id": k, "description": v.get("description", ""), "enabled": v.get("enabled", True)}
            for k, v in _registry.skills.items()
        ]
        return {"skills": skills, "count": len(skills)}

    @app.post("/api/skill/{skill_id}")
    async def execute_skill(skill_id: str, req: SkillRequest):
        meta = _registry.get_skill(skill_id)
        if not meta:
            raise HTTPException(status_code=404, detail=f"Skill \\'{skill_id}\\' 不存在")
        if not meta.get("enabled", True):
            raise HTTPException(status_code=400, detail=f"Skill \\'{skill_id}\\' 已停用")
        start = time.time()
        result = await _executor.execute(skill_id, req.input)
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "success": result.get("success", False),
            "skill_id": skill_id,
            "result": result.get("result", result.get("error", "")),
            "execution_time_ms": elapsed_ms,
        }

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    port = int(os.getenv("WEB_PORT", "2141"))
    print(f"🌐 ArkAgent Gateway 啟動中: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
'''
