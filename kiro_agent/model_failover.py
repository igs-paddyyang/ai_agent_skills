"""模型故障轉移 — 依序嘗試 failover 陣列中的備用模型。

當主模型失敗時，依照 model_failover 陣列順序嘗試備用模型。
成功切換時記錄事件，全部失敗時記錄 all_models_failed 事件。
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from kiro_agent.event_logger import EventLogger

logger = logging.getLogger(__name__)


class ModelFailover:
    """模型故障轉移管理器。

    Args:
        event_logger: 事件日誌記錄器，用於記錄切換與失敗事件。
    """

    def __init__(self, event_logger: EventLogger) -> None:
        self._event_logger = event_logger

    async def execute_with_failover(
        self,
        instance_name: str,
        failover_models: list[str],
        operation: Callable[[str], Any],
    ) -> Any:
        """嘗試以主模型執行操作，失敗則依序切換備用模型。

        Args:
            instance_name: Instance 名稱（用於事件記錄）。
            failover_models: 備用模型清單，依優先順序排列。
            operation: 接受模型名稱並執行操作的 async callable。
                       成功時回傳結果，失敗時 raise Exception。

        Returns:
            操作成功的回傳值，全部失敗時回傳 None。
        """
        for model in failover_models:
            try:
                result = await operation(model)
                # 非第一個模型 → 代表發生了切換
                if model != failover_models[0]:
                    self._event_logger.log(
                        "instance_started",
                        instance_name,
                        {"action": "model_switched", "model": model},
                    )
                    logger.info(
                        "Instance '%s' switched to model '%s'",
                        instance_name,
                        model,
                    )
                return result
            except Exception:
                logger.warning(
                    "Instance '%s' model '%s' failed, trying next",
                    instance_name,
                    model,
                )
                continue

        # 全部失敗
        self._event_logger.log(
            "instance_stopped",
            instance_name,
            {"action": "all_models_failed", "tried": failover_models},
        )
        logger.error(
            "Instance '%s' all models failed: %s", instance_name, failover_models
        )
        return None

    async def attempt_failover(
        self,
        instance_name: str,
        failover_models: list[str],
        try_model_fn: Callable[[str], bool],
    ) -> str | None:
        """簡化介面：嘗試 failover 模型清單，回傳成功的模型名稱。

        Args:
            instance_name: Instance 名稱。
            failover_models: 備用模型清單，依優先順序排列。
            try_model_fn: 接受模型名稱，回傳 True（成功）或 False（失敗）的 async callable。

        Returns:
            成功的模型名稱，全部失敗時回傳 None。
        """
        if not failover_models:
            self._event_logger.log(
                "instance_stopped",
                instance_name,
                {"action": "all_models_failed", "tried": []},
            )
            return None

        for model in failover_models:
            try:
                success = await try_model_fn(model)
                if success:
                    if model != failover_models[0]:
                        self._event_logger.log(
                            "instance_started",
                            instance_name,
                            {"action": "model_switched", "model": model},
                        )
                    return model
            except Exception:
                logger.warning(
                    "Instance '%s' model '%s' raised exception",
                    instance_name,
                    model,
                )
                continue

        # 全部失敗
        self._event_logger.log(
            "instance_stopped",
            instance_name,
            {"action": "all_models_failed", "tried": failover_models},
        )
        return None
