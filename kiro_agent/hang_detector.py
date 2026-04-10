"""掛起偵測 — 監控 Instance 活動狀態，超時無回應時發出警告。

HangDetector 追蹤每個 Instance 的最後活動時間，
check_all() 檢查所有 running Instance 是否超過 timeout_minutes。
"""

from __future__ import annotations

from datetime import datetime, timezone

from kiro_agent.config import HangDetectorConfig
from kiro_agent.event_logger import EventLogger
from kiro_agent.models import HangAlert


class HangDetector:
    """掛起偵測模組。

    Args:
        config: HangDetectorConfig，包含 enabled 與 timeout_minutes。
        event_logger: EventLogger 實例，用於記錄 hang_detected 事件。
        now_fn: 可選的時間函式，預設為 ``datetime.now(timezone.utc)``。
            供測試注入以控制時間。
    """

    def __init__(
        self,
        config: HangDetectorConfig,
        event_logger: EventLogger,
        *,
        now_fn: callable | None = None,
    ) -> None:
        self._config = config
        self._event_logger = event_logger
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._last_activity: dict[str, datetime] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_activity(self, instance_name: str) -> None:
        """更新指定 Instance 的最後活動時間為當前時間。

        Args:
            instance_name: Instance 名稱。
        """
        self._last_activity[instance_name] = self._now_fn()

    def check_all(self, running_instances: list[str]) -> list[HangAlert]:
        """檢查所有 running Instance 是否超過 timeout。

        Args:
            running_instances: 目前處於 running 狀態的 Instance 名稱清單。

        Returns:
            HangAlert 清單，每個 alert 代表一個超時的 Instance。
            若 detector 已停用（enabled=False），回傳空清單。
        """
        if not self._config.enabled:
            return []

        now = self._now_fn()
        timeout_seconds = self._config.timeout_minutes * 60
        alerts: list[HangAlert] = []

        for name in running_instances:
            last = self._last_activity.get(name)
            if last is None:
                # 從未記錄活動 — 視為剛啟動，先記錄當前時間
                self._last_activity[name] = now
                continue

            elapsed = (now - last).total_seconds()
            if elapsed > timeout_seconds:
                alert = HangAlert(
                    instance_name=name,
                    last_activity=last,
                    timeout_minutes=self._config.timeout_minutes,
                )
                alerts.append(alert)
                self._event_logger.log(
                    "hang_detected",
                    name,
                    {
                        "last_activity": last.isoformat(),
                        "timeout_minutes": self._config.timeout_minutes,
                        "elapsed_seconds": elapsed,
                    },
                )

        return alerts

    def is_hung(self, instance_name: str) -> bool:
        """檢查指定 Instance 是否已超過 timeout。

        Args:
            instance_name: Instance 名稱。

        Returns:
            True 表示已超時，False 表示正常或無記錄。
            若 detector 已停用，一律回傳 False。
        """
        if not self._config.enabled:
            return False

        last = self._last_activity.get(instance_name)
        if last is None:
            return False

        now = self._now_fn()
        elapsed = (now - last).total_seconds()
        return elapsed > self._config.timeout_minutes * 60
