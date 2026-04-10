"""Context 輪替 — 監控 context 使用率，超過閾值自動輪替。

ContextGuardian 讀取每個 Instance 的 statusline.json 取得 context 使用率，
超過 threshold（預設 80%）時產生 RotationSnapshot 並記錄事件。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kiro_agent.event_logger import EventLogger
from kiro_agent.models import RotationSnapshot


class ContextGuardian:
    """Context 輪替模組。

    Args:
        runtime_dir: 執行時資料目錄（``~/.kiro-agent/``）。
        event_logger: EventLogger 實例，用於記錄 context_rotated 事件。
        threshold: context 使用率閾值（百分比），預設 80.0。
        now_fn: 可選的時間函式，供測試注入以控制時間。
    """

    def __init__(
        self,
        runtime_dir: Path,
        event_logger: EventLogger,
        threshold: float = 80.0,
        *,
        now_fn: callable | None = None,
    ) -> None:
        self._runtime_dir = runtime_dir
        self._event_logger = event_logger
        self._threshold = threshold
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _read_statusline(self, instance_name: str) -> dict | None:
        """讀取指定 Instance 的 statusline.json。

        Args:
            instance_name: Instance 名稱。

        Returns:
            解析後的 dict，若檔案不存在或無法解析則回傳 None。
        """
        path = (
            self._runtime_dir / "instances" / instance_name / "statusline.json"
        )
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            if not isinstance(data, dict):
                return None
            return data
        except (OSError, json.JSONDecodeError, ValueError):
            return None

    def get_context_usage(self, instance_name: str) -> float | None:
        """取得指定 Instance 的 context 使用率百分比。

        Args:
            instance_name: Instance 名稱。

        Returns:
            context 使用率百分比，若無法讀取則回傳 None。
        """
        data = self._read_statusline(instance_name)
        if data is None:
            return None
        usage = data.get("context_usage_pct")
        if usage is None:
            return None
        try:
            return float(usage)
        except (TypeError, ValueError):
            return None

    def check_all(self, instance_names: list[str]) -> list[str]:
        """檢查所有 Instance，回傳超過閾值的名稱清單。

        Args:
            instance_names: 要檢查的 Instance 名稱清單。

        Returns:
            超過 threshold 的 Instance 名稱清單。
            statusline.json 不存在或無法解析的 Instance 會被跳過。
        """
        exceeded: list[str] = []
        for name in instance_names:
            usage = self.get_context_usage(name)
            if usage is not None and usage > self._threshold:
                exceeded.append(name)
        return exceeded

    def rotate(self, instance_name: str) -> RotationSnapshot:
        """為指定 Instance 產生 RotationSnapshot 並記錄事件。

        建立快照、儲存至 rotation_snapshot.md、記錄 context_rotated 事件。

        Args:
            instance_name: Instance 名稱。

        Returns:
            產生的 RotationSnapshot。
        """
        now = self._now_fn()
        snapshot = RotationSnapshot(
            instance_name=instance_name,
            timestamp=now,
            summary=f"Context rotation for {instance_name}",
            key_decisions=[],
            pending_tasks=[],
        )

        # 儲存 rotation_snapshot.md
        instance_dir = self._runtime_dir / "instances" / instance_name
        instance_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = instance_dir / "rotation_snapshot.md"
        snapshot_path.write_text(
            f"# Rotation Snapshot\n\n"
            f"- Instance: {snapshot.instance_name}\n"
            f"- Timestamp: {snapshot.timestamp.isoformat()}\n"
            f"- Summary: {snapshot.summary}\n",
            encoding="utf-8",
        )

        # 記錄事件
        self._event_logger.log(
            "context_rotated",
            instance_name,
            {
                "timestamp": now.isoformat(),
                "summary": snapshot.summary,
            },
        )

        return snapshot
