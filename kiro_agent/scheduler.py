"""排程系統 — cron 表達式觸發定時任務，SQLite 持久化。

Scheduler 使用 croniter 解析 cron 表達式，以 scheduler.db 持久化排程資料。
Fleet_Manager 重啟時可從 DB 恢復所有排程。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from croniter import croniter

from kiro_agent.models import ScheduleEntry

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEDULES_SCHEMA = """\
CREATE TABLE IF NOT EXISTS schedules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cron_expr       TEXT    NOT NULL,
    message         TEXT    NOT NULL,
    target_instance TEXT    NOT NULL,
    enabled         INTEGER NOT NULL DEFAULT 1,
    last_run        TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


# ---------------------------------------------------------------------------
# TriggeredSchedule — tick() 回傳的觸發結果
# ---------------------------------------------------------------------------

@dataclass
class TriggeredSchedule:
    """tick() 觸發的排程項目。"""

    schedule_id: int
    cron_expr: str
    message: str
    target_instance: str


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """排程系統 — cron 表達式觸發定時任務，SQLite 持久化。

    Args:
        db_path: SQLite 資料庫路徑，或 ``":memory:"`` 用於測試。
        event_logger: 可選的 EventLogger 實例，用於記錄 schedule_triggered 事件。
        conn: 可選的已建立連線（優先使用），方便測試注入。
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        event_logger: object | None = None,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        self._conn = conn if conn is not None else self._init_db(db_path)
        self._event_logger = event_logger

    # ------------------------------------------------------------------
    # DB init
    # ------------------------------------------------------------------

    @staticmethod
    def _init_db(db_path: str) -> sqlite3.Connection:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEDULES_SCHEMA)
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_schedule(
        self, cron: str, message: str, target: str
    ) -> int:
        """建立排程。

        Args:
            cron: cron 表達式（5 欄位）。
            message: 排程觸發時發送的訊息。
            target: 目標 Instance 名稱。

        Returns:
            新建排程的 id。

        Raises:
            ValueError: cron 表達式無效。
        """
        if not croniter.is_valid(cron):
            raise ValueError(f"Invalid cron expression: '{cron}'")

        cursor = self._conn.execute(
            "INSERT INTO schedules (cron_expr, message, target_instance) "
            "VALUES (?, ?, ?)",
            (cron, message, target),
        )
        self._conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    async def delete_schedule(self, schedule_id: int) -> bool:
        """刪除排程。

        Returns:
            True 若成功刪除，False 若 id 不存在。
        """
        cursor = self._conn.execute(
            "DELETE FROM schedules WHERE id = ?",
            (schedule_id,),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    async def list_schedules(self) -> list[ScheduleEntry]:
        """列出所有排程。"""
        rows = self._conn.execute(
            "SELECT id, cron_expr, message, target_instance, enabled, last_run "
            "FROM schedules ORDER BY id"
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    async def toggle_schedule(self, schedule_id: int) -> bool:
        """切換排程啟用狀態。

        Returns:
            切換後的 enabled 狀態。

        Raises:
            ValueError: schedule_id 不存在。
        """
        row = self._conn.execute(
            "SELECT enabled FROM schedules WHERE id = ?",
            (schedule_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Schedule id {schedule_id} not found")

        new_enabled = 0 if row["enabled"] else 1
        self._conn.execute(
            "UPDATE schedules SET enabled = ? WHERE id = ?",
            (new_enabled, schedule_id),
        )
        self._conn.commit()
        return bool(new_enabled)

    async def tick(
        self, now: datetime | None = None
    ) -> list[TriggeredSchedule]:
        """檢查所有啟用排程，觸發匹配當前時間的排程。

        Args:
            now: 當前時間（預設 UTC now），方便測試注入。

        Returns:
            本次 tick 觸發的排程清單。
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # 取得當前分鐘的起始時間（截斷到分鐘）
        current_minute = now.replace(second=0, microsecond=0)
        current_minute_str = current_minute.strftime("%Y-%m-%dT%H:%M")

        rows = self._conn.execute(
            "SELECT id, cron_expr, message, target_instance, last_run "
            "FROM schedules WHERE enabled = 1"
        ).fetchall()

        triggered: list[TriggeredSchedule] = []

        for row in rows:
            cron_expr = row["cron_expr"]
            last_run = row["last_run"]

            # 避免同一分鐘重複觸發
            if last_run is not None and last_run.startswith(current_minute_str):
                continue

            # 使用 croniter 判斷 cron 是否匹配當前分鐘
            if self._cron_matches(cron_expr, current_minute):
                # 更新 last_run
                self._conn.execute(
                    "UPDATE schedules SET last_run = ? WHERE id = ?",
                    (current_minute.isoformat(), row["id"]),
                )

                triggered.append(
                    TriggeredSchedule(
                        schedule_id=row["id"],
                        cron_expr=cron_expr,
                        message=row["message"],
                        target_instance=row["target_instance"],
                    )
                )

                # 記錄事件
                if self._event_logger is not None:
                    try:
                        self._event_logger.log(
                            "schedule_triggered",
                            row["target_instance"],
                            {
                                "schedule_id": row["id"],
                                "cron_expr": cron_expr,
                                "message": row["message"],
                            },
                        )
                    except Exception:
                        pass  # 不中斷主流程

        if triggered:
            self._conn.commit()

        return triggered

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cron_matches(cron_expr: str, dt: datetime) -> bool:
        """判斷 cron 表達式是否匹配指定時間（精確到分鐘）。

        使用 croniter.match 判斷 dt 是否為 cron 表達式的匹配時間。
        """
        return croniter.match(cron_expr, dt)

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> ScheduleEntry:
        """將 sqlite3.Row 轉為 ScheduleEntry。"""
        last_run = None
        if row["last_run"] is not None:
            try:
                last_run = datetime.fromisoformat(row["last_run"])
            except (ValueError, TypeError):
                pass
        return ScheduleEntry(
            id=row["id"],
            cron_expr=row["cron_expr"],
            message=row["message"],
            target_instance=row["target_instance"],
            enabled=bool(row["enabled"]),
            last_run=last_run,
        )
