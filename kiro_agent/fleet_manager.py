"""艦隊管理核心 — 管理所有 Agent Instance 的生命週期。

FleetManager 負責：
- 啟動/停止整個艦隊
- 建立/啟動/停止/刪除個別 Instance
- Instance 名稱唯一性驗證
- tmux crash 自動重啟（最多 3 次，間隔 5s/15s/45s）
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from kiro_agent.backend_adapter import BackendAdapter, get_adapter
from kiro_agent.channel_router import ChannelRouter
from kiro_agent.config import FleetConfig, InstanceConfig
from kiro_agent.event_logger import EventLogger
from kiro_agent.models import InstanceError, InstanceState, InstanceStatus

logger = logging.getLogger(__name__)

# 重試間隔：5×3^0, 5×3^1, 5×3^2 = 5, 15, 45 秒
_MAX_RETRIES = 3


class FleetManager:
    """艦隊管理核心。

    Args:
        config: 艦隊配置。
        event_logger: 事件日誌記錄器。
    """

    def __init__(self, config: FleetConfig, event_logger: EventLogger) -> None:
        self.config = config
        self.event_logger = event_logger
        self.instances: dict[str, InstanceState] = {}
        self.adapters: dict[str, BackendAdapter] = {}
        self.channel_router: ChannelRouter | None = None
        self._retry_counts: dict[str, int] = {}
        self._restart_tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # 靜態工具
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_retry_interval(attempt: int) -> int | None:
        """計算第 N 次重試的等待間隔（秒）。

        公式：5 × 3^attempt（attempt 從 0 開始）。
        超過最大重試次數時回傳 None。

        Args:
            attempt: 重試次數（0-based）。

        Returns:
            等待秒數，或 None 表示不再重試。
        """
        if attempt < 0 or attempt >= _MAX_RETRIES:
            return None
        return 5 * (3 ** attempt)

    # ------------------------------------------------------------------
    # 艦隊啟動 / 停止
    # ------------------------------------------------------------------

    async def start_fleet(self) -> None:
        """啟動艦隊。

        流程：
        1. 為每個 Instance 建立對應的 BackendAdapter
        2. 啟動所有 auto_start 的 Instance
        3. 初始化並啟動 ChannelRouter（Telegram Bot）
        """
        logger.info("正在啟動艦隊...")

        # 1. 初始化 Adapters 與 InstanceState
        for inst_cfg in self.config.instances:
            adapter = get_adapter(inst_cfg.backend)
            self.adapters[inst_cfg.name] = adapter
            self.instances[inst_cfg.name] = InstanceState(
                name=inst_cfg.name,
                status=InstanceStatus.STOPPED,
                backend=inst_cfg.backend,
                model=inst_cfg.model,
            )

        # 2. 啟動 auto_start Instances
        for inst_cfg in self.config.instances:
            if inst_cfg.auto_start:
                await self.start_instance(inst_cfg.name)

        # 3. 啟動 ChannelRouter
        self.channel_router = ChannelRouter(
            fleet_manager=self,
            config=self.config,
            event_logger=self.event_logger,
        )
        await self.channel_router.start()

        # 4. 註冊已有 topic_id 的 Instance 映射
        for state in self.instances.values():
            if state.topic_id is not None:
                self.channel_router.register_topic(state.topic_id, state.name)

        started = sum(
            1
            for s in self.instances.values()
            if s.status == InstanceStatus.RUNNING
        )
        logger.info("艦隊已啟動（%d/%d instances running）", started, len(self.instances))

    async def stop_fleet(self) -> None:
        """停止艦隊。

        流程：
        1. 取消所有進行中的重啟任務
        2. 停止所有 running 的 Instance
        3. 停止 ChannelRouter
        """
        logger.info("正在停止艦隊...")

        # 取消重啟任務
        for task in self._restart_tasks.values():
            task.cancel()
        self._restart_tasks.clear()

        # 停止所有 running Instance
        running = [
            name
            for name, state in self.instances.items()
            if state.status == InstanceStatus.RUNNING
        ]
        for name in running:
            try:
                await self.stop_instance(name)
            except Exception:
                logger.exception("停止 Instance '%s' 時發生錯誤", name)

        # 停止 ChannelRouter
        if self.channel_router is not None:
            await self.channel_router.stop()
            self.channel_router = None

        logger.info("艦隊已停止")

    # ------------------------------------------------------------------
    # Instance CRUD
    # ------------------------------------------------------------------

    async def create_instance(
        self,
        name: str,
        project: str,
        **kwargs: object,
    ) -> None:
        """建立新的 Instance。

        Args:
            name: Instance 名稱（必須唯一）。
            project: project_roots 中的 key。
            **kwargs: 其他 InstanceConfig 欄位（backend, model, description 等）。

        Raises:
            InstanceError: 名稱已存在。
        """
        if name in self.instances:
            raise InstanceError(f"Instance '{name}' already exists")

        # 建構 InstanceConfig
        backend = str(kwargs.get("backend", self.config.defaults.get("backend", "kiro-cli")))
        model = str(kwargs.get("model", self.config.defaults.get("model", "auto")))
        description = str(kwargs.get("description", ""))
        auto_start = bool(kwargs.get("auto_start", False))

        inst_cfg = InstanceConfig(
            name=name,
            project=project,
            backend=backend,
            model=model,
            description=description,
            auto_start=auto_start,
        )

        # 初始化 Adapter 與 State
        adapter = get_adapter(backend)
        self.adapters[name] = adapter
        self.instances[name] = InstanceState(
            name=name,
            status=InstanceStatus.STOPPED,
            backend=backend,
            model=model,
        )

        # 加入配置
        self.config.instances.append(inst_cfg)

        # 建立 Telegram Topic 並註冊映射
        if self.channel_router is not None:
            topic_id = await self.channel_router.create_topic(name)
            if topic_id:
                self.channel_router.register_topic(topic_id, name)
                self.instances[name].topic_id = topic_id

        self.event_logger.log(
            "instance_started",
            instance_name=name,
            data={"action": "created", "project": project, "backend": backend},
        )
        logger.info("已建立 Instance '%s'（project=%s, backend=%s）", name, project, backend)

    async def start_instance(self, name: str) -> None:
        """啟動指定的 Instance。

        Args:
            name: Instance 名稱。

        Raises:
            InstanceError: Instance 不存在或已在 running 狀態。
        """
        state = self.instances.get(name)
        if state is None:
            raise InstanceError(f"Instance '{name}' not found")
        if state.status == InstanceStatus.RUNNING:
            raise InstanceError(f"Instance '{name}' is already running")

        # 找到對應的 InstanceConfig
        inst_cfg = self._get_instance_config(name)
        adapter = self.adapters[name]

        # 解析工作目錄
        project_path = self.config.project_roots.get(inst_cfg.project, "")
        work_dir = Path(project_path)

        state.status = InstanceStatus.STARTING
        try:
            await adapter.start_session(inst_cfg, work_dir)
            state.status = InstanceStatus.RUNNING
            state.tmux_session = f"ka-{name}"
            self._retry_counts.pop(name, None)
            self.event_logger.log("instance_started", instance_name=name)
            logger.info("Instance '%s' 已啟動", name)
        except Exception as exc:
            state.status = InstanceStatus.STOPPED
            logger.error("啟動 Instance '%s' 失敗: %s", name, exc)
            raise

    async def stop_instance(self, name: str) -> None:
        """停止指定的 Instance。

        Args:
            name: Instance 名稱。

        Raises:
            InstanceError: Instance 不存在。
        """
        state = self.instances.get(name)
        if state is None:
            raise InstanceError(f"Instance '{name}' not found")

        adapter = self.adapters.get(name)
        if adapter is not None and state.status in (
            InstanceStatus.RUNNING,
            InstanceStatus.STARTING,
            InstanceStatus.HUNG,
        ):
            try:
                await adapter.stop_session(name)
            except Exception:
                logger.exception("停止 Instance '%s' 的 tmux session 時發生錯誤", name)

        state.status = InstanceStatus.STOPPED
        state.tmux_session = None
        self.event_logger.log("instance_stopped", instance_name=name)
        logger.info("Instance '%s' 已停止", name)

    async def delete_instance(self, name: str) -> None:
        """刪除指定的 Instance。

        停止 Instance → 移除狀態與 Adapter → 從配置中移除。

        Args:
            name: Instance 名稱。

        Raises:
            InstanceError: Instance 不存在。
        """
        if name not in self.instances:
            raise InstanceError(f"Instance '{name}' not found")

        # 先停止
        state = self.instances[name]
        if state.status != InstanceStatus.STOPPED:
            await self.stop_instance(name)

        # 取消重啟任務
        task = self._restart_tasks.pop(name, None)
        if task is not None:
            task.cancel()

        # 移除 Topic 映射
        if self.channel_router is not None:
            self.channel_router.unregister_topic(name)

        # 移除狀態與 Adapter
        del self.instances[name]
        self.adapters.pop(name, None)
        self._retry_counts.pop(name, None)

        # 從配置中移除
        self.config.instances = [
            cfg for cfg in self.config.instances if cfg.name != name
        ]

        logger.info("已刪除 Instance '%s'", name)

    async def restart_instance(self, name: str) -> None:
        """重啟指定的 Instance（stop → start）。

        Args:
            name: Instance 名稱。

        Raises:
            InstanceError: Instance 不存在。
        """
        await self.stop_instance(name)
        await self.start_instance(name)

    # ------------------------------------------------------------------
    # 訊息傳送
    # ------------------------------------------------------------------

    async def send_message_to_instance(self, name: str, message: str) -> None:
        """傳送訊息到指定 Instance 的 tmux session。

        Args:
            name: Instance 名稱。
            message: 要傳送的訊息。

        Raises:
            InstanceError: Instance 不存在或未在 running 狀態。
        """
        state = self.instances.get(name)
        if state is None:
            raise InstanceError(f"Instance '{name}' not found")
        if state.status != InstanceStatus.RUNNING:
            raise InstanceError(f"Instance '{name}' is not running")

        adapter = self.adapters[name]
        await adapter.send_message(name, message)

        self.event_logger.log(
            "message_sent",
            instance_name=name,
            data={"length": len(message)},
        )

    async def send_tool_decision(self, name: str, decision: str) -> None:
        """傳送工具使用決策到指定 Instance。

        Args:
            name: Instance 名稱。
            decision: "allow" 或 "deny"。
        """
        state = self.instances.get(name)
        if state is None:
            raise InstanceError(f"Instance '{name}' not found")

        adapter = self.adapters.get(name)
        if adapter is not None and state.status == InstanceStatus.RUNNING:
            await adapter.send_message(name, decision)

        self.event_logger.log(
            "tool_decision",
            instance_name=name,
            data={"decision": decision},
        )

    # ------------------------------------------------------------------
    # Crash 偵測與自動重啟
    # ------------------------------------------------------------------

    async def handle_crash(self, name: str) -> None:
        """處理 Instance crash，嘗試自動重啟。

        最多重試 3 次，間隔 5s / 15s / 45s。
        超過重試上限後標記為 crashed。

        Args:
            name: 發生 crash 的 Instance 名稱。
        """
        attempt = self._retry_counts.get(name, 0)
        interval = self.calculate_retry_interval(attempt)

        if interval is None:
            # 超過重試上限
            state = self.instances.get(name)
            if state is not None:
                state.status = InstanceStatus.STOPPED
            self.event_logger.log(
                "instance_crashed",
                instance_name=name,
                data={"attempts": attempt, "action": "gave_up"},
            )
            logger.error(
                "Instance '%s' crash 重啟失敗（已重試 %d 次），標記為 crashed",
                name,
                attempt,
            )
            self._retry_counts.pop(name, None)
            return

        self._retry_counts[name] = attempt + 1
        logger.warning(
            "Instance '%s' crash 偵測，%d 秒後重試（第 %d/%d 次）",
            name,
            interval,
            attempt + 1,
            _MAX_RETRIES,
        )

        self.event_logger.log(
            "instance_crashed",
            instance_name=name,
            data={
                "attempt": attempt + 1,
                "interval": interval,
                "action": "retrying",
            },
        )

        await asyncio.sleep(interval)

        try:
            await self.start_instance(name)
            logger.info("Instance '%s' crash 重啟成功（第 %d 次）", name, attempt + 1)
        except Exception:
            logger.exception("Instance '%s' crash 重啟失敗", name)
            await self.handle_crash(name)

    # ------------------------------------------------------------------
    # 內部輔助
    # ------------------------------------------------------------------

    def _get_instance_config(self, name: str) -> InstanceConfig:
        """根據名稱取得 InstanceConfig。"""
        for cfg in self.config.instances:
            if cfg.name == name:
                return cfg
        raise InstanceError(f"InstanceConfig for '{name}' not found")
