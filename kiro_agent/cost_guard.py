"""費用控管 — 追蹤 API 使用費用，達上限自動暫停 Instance。

CostGuard 封裝 cost_records 表的讀寫操作，
依 timezone 計算 date_key，支援每日重置與閾值警告。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from kiro_agent.config import CostGuardConfig
from kiro_agent.event_logger import EventLogger
from kiro_agent.models import CostAlert


class CostGuard:
    """費用控管模組。

    Args:
        config: CostGuardConfig，包含 daily_limit_usd、warn_at_percentage、timezone。
        db_conn: SQLite 連線（需已建立 cost_records 表）。
        event_logger: EventLogger 實例，用於記錄 cost_warning / cost_limit_reached 事件。
    """

    def __init__(
        self,
        config: CostGuardConfig,
        db_conn: sqlite3.Connection,
        event_logger: EventLogger,
    ) -> None:
        self._config = config
        self._conn = db_conn
        self._event_logger = event_logger

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_cost(self, instance_name: str, amount_usd: float) -> None:
        """記錄一筆 API 費用。

        Args:
            instance_name: Instance 名稱。
            amount_usd: 費用金額（USD）。
        """
        date_key = self._today_key()
        self._conn.execute(
            "INSERT INTO cost_records (instance_name, amount_usd, date_key) "
            "VALUES (?, ?, ?)",
            (instance_name, amount_usd, date_key),
        )
        self._conn.commit()

    def get_daily_cost(self, instance_name: str) -> float:
        """取得指定 Instance 今日累計費用。

        Args:
            instance_name: Instance 名稱。

        Returns:
            今日累計費用（USD），無記錄時回傳 0.0。
        """
        date_key = self._today_key()
        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount_usd), 0.0) AS total "
            "FROM cost_records WHERE date_key = ? AND instance_name = ?",
            (date_key, instance_name),
        ).fetchone()
        return float(row["total"]) if row else 0.0

    def check_limits(self, instance_names: list[str] | None = None) -> list[CostAlert]:
        """檢查所有（或指定）Instance 的費用是否超過閾值。

        Args:
            instance_names: 要檢查的 Instance 名稱清單。
                若為 None，則查詢今日有費用記錄的所有 Instance。

        Returns:
            CostAlert 清單，每個 alert 包含 instance_name、daily_cost_usd、
            limit_usd 與 alert_type（"warning" 或 "limit_reached"）。
        """
        if instance_names is None:
            instance_names = self._instances_with_cost_today()

        limit = self._config.daily_limit_usd
        warn_threshold = limit * self._config.warn_at_percentage / 100.0
        alerts: list[CostAlert] = []

        for name in instance_names:
            cost = self.get_daily_cost(name)
            if cost >= limit:
                alert = CostAlert(
                    instance_name=name,
                    daily_cost_usd=cost,
                    limit_usd=limit,
                    alert_type="limit_reached",
                )
                alerts.append(alert)
                self._event_logger.log(
                    "cost_limit_reached",
                    name,
                    {"daily_cost_usd": cost, "limit_usd": limit},
                )
            elif cost >= warn_threshold:
                alert = CostAlert(
                    instance_name=name,
                    daily_cost_usd=cost,
                    limit_usd=limit,
                    alert_type="warning",
                )
                alerts.append(alert)
                self._event_logger.log(
                    "cost_warning",
                    name,
                    {"daily_cost_usd": cost, "warn_threshold_usd": warn_threshold},
                )

        return alerts

    def reset_daily(self) -> None:
        """每日重置 — 無需刪除資料，因為查詢以 date_key 區分。

        此方法為語意佔位符，可用於未來擴展（如清理舊記錄）。
        """
        # 查詢以 date_key 為基礎，新的一天自動使用新的 date_key，
        # 因此不需要實際刪除或重置操作。

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _today_key(self) -> str:
        """回傳今日的 date_key（YYYY-MM-DD），依 config timezone 計算。"""
        tz = ZoneInfo(self._config.timezone)
        return datetime.now(tz).strftime("%Y-%m-%d")

    def _instances_with_cost_today(self) -> list[str]:
        """查詢今日有費用記錄的所有 Instance 名稱。"""
        date_key = self._today_key()
        rows = self._conn.execute(
            "SELECT DISTINCT instance_name FROM cost_records WHERE date_key = ?",
            (date_key,),
        ).fetchall()
        return [row["instance_name"] for row in rows]
