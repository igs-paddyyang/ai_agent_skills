"""kiro-agent AI CLI 後端抽象層。

定義 BackendAdapter ABC 與 BACKEND_REGISTRY，
提供 get_adapter() 工廠函式根據名稱取得 Adapter 實例。
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from kiro_agent.config import InstanceConfig
from kiro_agent.models import BackendError, InstanceState, InstanceStatus

logger = logging.getLogger(__name__)

# tmux session 名稱前綴，避免與使用者的 tmux session 衝突
_TMUX_PREFIX = "ka-"


def _tmux_session_name(instance_name: str) -> str:
    """產生 tmux session 名稱。"""
    return f"{_TMUX_PREFIX}{instance_name}"


class BackendAdapter(ABC):
    """所有 AI CLI 後端的統一介面。"""

    @abstractmethod
    async def start_session(self, instance: InstanceConfig, work_dir: Path) -> None:
        """在 tmux session 中啟動 CLI。"""
        ...

    @abstractmethod
    async def send_message(self, instance_name: str, message: str) -> None:
        """透過 tmux send-keys 傳送訊息到 CLI。"""
        ...

    @abstractmethod
    async def stop_session(self, instance_name: str) -> None:
        """優雅終止 tmux session。"""
        ...

    @abstractmethod
    async def get_status(self, instance_name: str) -> InstanceState:
        """取得 Instance 狀態（running/stopped/hung）。"""
        ...


# ---------------------------------------------------------------------------
# Helper: 執行 tmux 命令
# ---------------------------------------------------------------------------


async def _run_tmux(*args: str) -> tuple[int, str, str]:
    """執行 tmux 子命令，回傳 (returncode, stdout, stderr)。"""
    proc = await asyncio.create_subprocess_exec(
        "tmux",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    return (
        proc.returncode or 0,
        stdout_bytes.decode("utf-8", errors="replace").strip(),
        stderr_bytes.decode("utf-8", errors="replace").strip(),
    )


# ---------------------------------------------------------------------------
# TmuxBackendAdapter — 共用 tmux 操作基底類別
# ---------------------------------------------------------------------------


class TmuxBackendAdapter(BackendAdapter):
    """所有基於 tmux 的後端共用邏輯。

    子類別只需定義 `cli_command` 與 `backend_name`，
    即可獲得完整的 start/send/stop/status 實作。
    """

    cli_command: str = ""       # 子類別覆寫，例如 "claude", "gemini"
    backend_name: str = ""      # 子類別覆寫，例如 "claude-code"

    def _build_cli_cmd(self, instance: InstanceConfig) -> str:
        """建構 CLI 啟動命令。子類別可覆寫以加入額外參數。"""
        return self.cli_command

    async def start_session(self, instance: InstanceConfig, work_dir: Path) -> None:
        """在 tmux session 中啟動 CLI。"""
        work_dir = Path(work_dir)
        session_name = _tmux_session_name(instance.name)

        # tmux new-session
        rc, _, stderr = await _run_tmux(
            "new-session", "-d", "-s", session_name, "-c", str(work_dir),
        )
        if rc != 0:
            raise BackendError(
                backend=self.backend_name,
                error_type="tmux_error",
                suggestion=f"無法建立 tmux session '{session_name}': {stderr}",
            )

        # tmux send-keys 啟動 CLI
        cli_cmd = self._build_cli_cmd(instance)
        rc, _, stderr = await _run_tmux(
            "send-keys", "-t", session_name, cli_cmd, "Enter",
        )
        if rc != 0:
            raise BackendError(
                backend=self.backend_name,
                error_type="tmux_error",
                suggestion=f"無法在 tmux session 中啟動 {self.cli_command}: {stderr}",
            )

        logger.info(
            "%s: 已啟動 session '%s' (cmd=%s)",
            type(self).__name__, session_name, cli_cmd,
        )

    async def send_message(self, instance_name: str, message: str) -> None:
        """透過 tmux send-keys 傳送訊息。"""
        session_name = _tmux_session_name(instance_name)
        escaped = _escape_for_tmux(message)

        rc, _, stderr = await _run_tmux(
            "send-keys", "-t", session_name, escaped, "Enter",
        )
        if rc != 0:
            raise BackendError(
                backend=self.backend_name,
                error_type="send_failed",
                suggestion=f"無法傳送訊息到 session '{session_name}': {stderr}",
            )

    async def stop_session(self, instance_name: str) -> None:
        """優雅終止 tmux session：先送 /exit，再 kill-session。"""
        session_name = _tmux_session_name(instance_name)

        # 嘗試優雅退出
        await _run_tmux("send-keys", "-t", session_name, "/exit", "Enter")
        await asyncio.sleep(1.0)

        # 檢查 session 是否還在，若在則強制 kill
        rc, _, _ = await _run_tmux("has-session", "-t", session_name)
        if rc == 0:
            await _run_tmux("kill-session", "-t", session_name)
            logger.info("%s: 已強制終止 session '%s'", type(self).__name__, session_name)
        else:
            logger.info("%s: session '%s' 已優雅退出", type(self).__name__, session_name)

    async def get_status(self, instance_name: str) -> InstanceState:
        """檢查 tmux session 存活狀態。"""
        session_name = _tmux_session_name(instance_name)

        rc, _, _ = await _run_tmux("has-session", "-t", session_name)
        status = InstanceStatus.RUNNING if rc == 0 else InstanceStatus.STOPPED

        return InstanceState(
            name=instance_name,
            status=status,
            backend=self.backend_name,
            model="auto",
            tmux_session=session_name,
        )


# ---------------------------------------------------------------------------
# KiroCliAdapter
# ---------------------------------------------------------------------------


class KiroCliAdapter(TmuxBackendAdapter):
    """Kiro CLI 後端 — 支援 steering、skills、fleet-context.md 注入。"""

    cli_command = "kiro-cli"
    backend_name = "kiro-cli"

    supported_models: list[str] = [
        "auto",
        "claude-sonnet-4.5",
        "claude-sonnet-4",
        "claude-haiku-4.5",
    ]

    def _build_cli_cmd(self, instance: InstanceConfig) -> str:
        """Kiro CLI 需要 --model 參數。"""
        return f"kiro-cli --model {instance.model}"

    async def start_session(self, instance: InstanceConfig, work_dir: Path) -> None:
        """啟動 Kiro CLI tmux session。

        1. 檢查 .kiro/steering/ 存在
        2. 驗證模型
        3. 寫入 fleet-context.md
        4. 委託 TmuxBackendAdapter 處理 tmux 操作
        """
        work_dir = Path(work_dir)
        steering_dir = work_dir / ".kiro" / "steering"
        if not steering_dir.is_dir():
            raise BackendError(
                backend="kiro-cli",
                error_type="missing_steering",
                suggestion=(
                    f"工作目錄 '{work_dir}' 缺少 .kiro/steering/ 目錄，"
                    "請先執行 kiro init 或手動建立"
                ),
            )

        # 驗證模型
        model = instance.model
        if model not in self.supported_models:
            raise BackendError(
                backend="kiro-cli",
                error_type="unsupported_model",
                suggestion=(
                    f"不支援的模型 '{model}'，"
                    f"可用模型: {', '.join(self.supported_models)}"
                ),
            )

        # 寫入 fleet-context.md
        fleet_context_path = steering_dir / "fleet-context.md"
        context_content = self.generate_fleet_context(instance)
        fleet_context_path.write_text(context_content, encoding="utf-8")

        # 委託基底類別處理 tmux new-session + send-keys
        await super().start_session(instance, work_dir)

    @staticmethod
    def generate_fleet_context(
        instance: InstanceConfig,
        peers: list[InstanceConfig] | None = None,
    ) -> str:
        """產生 fleet-context.md 內容。

        Args:
            instance: 當前 Instance 配置。
            peers: 其他 Instance 配置清單（不含自身）。

        Returns:
            Markdown 格式的 fleet context 內容。
        """
        lines: list[str] = [
            "# Fleet Context",
            "",
            "## Identity",
            "",
            f"- **Name:** {instance.name}",
            f"- **Backend:** {instance.backend}",
            f"- **Model:** {instance.model}",
        ]
        if instance.description:
            lines.append(f"- **Description:** {instance.description}")

        lines.extend(["", "## Peers", ""])

        if peers:
            for peer in peers:
                desc = f" — {peer.description}" if peer.description else ""
                lines.append(f"- **{peer.name}** ({peer.backend}){desc}")
        else:
            lines.append("- (no peers configured)")

        lines.extend([
            "",
            "## Collaboration Rules",
            "",
            "1. Use MCP tools (list_instances, delegate_task, send_to_instance) to collaborate with peers.",
            "2. Always report_result back to the requester when completing a delegated task.",
            "3. Do not modify files outside your assigned project directory.",
            "4. Coordinate with peers before making cross-project changes.",
            "",
        ])

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: tmux 訊息跳脫
# ---------------------------------------------------------------------------


def _escape_for_tmux(message: str) -> str:
    """跳脫 tmux send-keys 的特殊字元。

    tmux send-keys 會解釋某些特殊字元（如 ;、#），
    需要用引號包裹或跳脫來避免誤解。
    """
    # 跳脫反斜線和雙引號
    escaped = message.replace("\\", "\\\\").replace('"', '\\"')
    # 跳脫 tmux 特殊字元：; 和 #
    escaped = escaped.replace(";", "\\;")
    return escaped


# ---------------------------------------------------------------------------
# 其他 Backend Adapter 實作
# ---------------------------------------------------------------------------


class ClaudeCodeAdapter(TmuxBackendAdapter):
    """Claude Code CLI 後端。"""

    cli_command = "claude"
    backend_name = "claude-code"


class GeminiCliAdapter(TmuxBackendAdapter):
    """Gemini CLI 後端。"""

    cli_command = "gemini"
    backend_name = "gemini-cli"


class CodexAdapter(TmuxBackendAdapter):
    """Codex CLI 後端。"""

    cli_command = "codex"
    backend_name = "codex"


class OpenCodeAdapter(TmuxBackendAdapter):
    """OpenCode CLI 後端。"""

    cli_command = "opencode"
    backend_name = "opencode"


# ---------------------------------------------------------------------------
# Registry & Factory
# ---------------------------------------------------------------------------

BACKEND_REGISTRY: dict[str, type[BackendAdapter]] = {
    "kiro-cli": KiroCliAdapter,
    "claude-code": ClaudeCodeAdapter,
    "gemini-cli": GeminiCliAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
}


def get_adapter(backend_name: str) -> BackendAdapter:
    """根據名稱取得 BackendAdapter 實例。

    Args:
        backend_name: 後端名稱（須存在於 BACKEND_REGISTRY）。

    Returns:
        對應的 BackendAdapter 實例。

    Raises:
        BackendError: 後端名稱不存在於 BACKEND_REGISTRY。
    """
    adapter_cls = BACKEND_REGISTRY.get(backend_name)
    if adapter_cls is None:
        available = ", ".join(sorted(BACKEND_REGISTRY.keys()))
        raise BackendError(
            backend=backend_name,
            error_type="not_found",
            suggestion=f"可用的後端: {available}",
        )
    return adapter_cls()
