"""Telegram Forum Topic 訊息路由器。

接收 Telegram 訊息，根據 Topic ID 路由到對應的 Agent Instance。
實作存取控制（allowed_users 白名單）與事件日誌記錄。
"""

from __future__ import annotations

import logging
import os
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from kiro_agent.config import FleetConfig
from kiro_agent.event_logger import EventLogger

logger = logging.getLogger(__name__)


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """將文字分割為不超過 max_length 的多個片段。

    分割策略（優先順序）：
    1. 在換行符處分割
    2. 在空格處分割
    3. 在 max_length 邊界強制分割

    串接所有片段後必須等於原始字串。

    Args:
        text: 要分割的文字。
        max_length: 每個片段的最大長度（預設 4096）。

    Returns:
        分割後的字串清單。空字串回傳 ``[""]``。
    """
    if max_length <= 0:
        raise ValueError("max_length must be positive")

    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # 嘗試在 max_length 範圍內找換行符
        split_pos = remaining.rfind("\n", 0, max_length)
        if split_pos > 0:
            # 換行符留在前一段末尾
            chunks.append(remaining[: split_pos + 1])
            remaining = remaining[split_pos + 1 :]
            continue

        # 嘗試在 max_length 範圍內找空格
        split_pos = remaining.rfind(" ", 0, max_length)
        if split_pos > 0:
            # 空格留在前一段末尾
            chunks.append(remaining[: split_pos + 1])
            remaining = remaining[split_pos + 1 :]
            continue

        # 無好的分割點，強制在 max_length 處切割
        chunks.append(remaining[:max_length])
        remaining = remaining[max_length:]

    return chunks


class ChannelRouter:
    """Telegram Forum Topic 訊息路由器。

    將 Telegram Group 中各 Forum Topic 的訊息路由到對應的 Agent Instance。
    支援存取控制（locked 模式下僅允許白名單使用者）。

    Args:
        fleet_manager: FleetManager 實例（typed as Any 避免循環匯入）。
        config: 艦隊配置。
        event_logger: 事件日誌記錄器。
    """

    def __init__(
        self,
        fleet_manager: Any,
        config: FleetConfig,
        event_logger: EventLogger | None = None,
    ) -> None:
        self.fleet_manager = fleet_manager
        self.config = config
        self.event_logger = event_logger or EventLogger()
        self.topic_instance_map: dict[int, str] = {}  # topic_id -> instance_name
        self._application: Application | None = None

    # ------------------------------------------------------------------
    # Topic-Instance 路由映射
    # ------------------------------------------------------------------

    def register_topic(self, topic_id: int, instance_name: str) -> None:
        """將 topic_id 映射到 instance_name。

        Args:
            topic_id: Telegram Forum Topic 的 ID。
            instance_name: 對應的 Instance 名稱。
        """
        self.topic_instance_map[topic_id] = instance_name
        logger.info(
            "Registered topic mapping: topic_id=%d -> '%s'",
            topic_id,
            instance_name,
        )

    def unregister_topic(self, instance_name: str) -> None:
        """移除指定 Instance 的 topic 映射。

        Args:
            instance_name: 要移除映射的 Instance 名稱。
        """
        to_remove = [
            tid
            for tid, name in self.topic_instance_map.items()
            if name == instance_name
        ]
        for tid in to_remove:
            del self.topic_instance_map[tid]
            logger.info(
                "Unregistered topic mapping: topic_id=%d (was '%s')",
                tid,
                instance_name,
            )

    def get_instance_for_topic(self, topic_id: int) -> str | None:
        """根據 topic_id 查找對應的 Instance 名稱。

        Args:
            topic_id: Telegram Forum Topic 的 ID。

        Returns:
            對應的 Instance 名稱，或 None 表示未映射。
        """
        return self.topic_instance_map.get(topic_id)

    # ------------------------------------------------------------------
    # 存取控制
    # ------------------------------------------------------------------

    def is_user_allowed(self, user_id: int) -> bool:
        """檢查使用者是否在白名單中。

        當 access.mode 為 "locked" 時，僅允許 allowed_users 中的使用者。
        其他模式（如 "open"）允許所有使用者。
        """
        if self.config.access.mode != "locked":
            return True
        return user_id in self.config.access.allowed_users

    # ------------------------------------------------------------------
    # Telegram Bot 啟動
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """啟動 Telegram Bot polling。

        從環境變數讀取 Bot Token（由 config.channel["bot_token_env"] 指定），
        建立 Application 並註冊 handler，開始 polling。
        """
        bot_token_env = self.config.channel.get("bot_token_env", "TELEGRAM_BOT_TOKEN")
        bot_token = os.environ.get(bot_token_env, "")
        if not bot_token:
            logger.error(
                "Bot token not found in environment variable '%s'", bot_token_env
            )
            return

        self._application = (
            Application.builder().token(bot_token).build()
        )

        # 註冊訊息處理器（文字 + 語音等所有訊息）
        self._application.add_handler(
            MessageHandler(filters.ALL, self.on_message)
        )
        # 註冊 inline button 回調處理器
        self._application.add_handler(
            CallbackQueryHandler(self.on_callback_query)
        )

        logger.info("Starting Telegram Bot polling...")
        await self._application.initialize()
        await self._application.start()
        await self._application.updater.start_polling()  # type: ignore[union-attr]

    async def stop(self) -> None:
        """停止 Telegram Bot polling。"""
        if self._application and self._application.updater:
            await self._application.updater.stop()
            await self._application.stop()
            await self._application.shutdown()
            self._application = None

    # ------------------------------------------------------------------
    # 訊息處理主流程
    # ------------------------------------------------------------------

    async def on_message(self, update: Update, context: Any) -> None:
        """訊息處理主流程。

        1. 驗證 user_id 在 allowed_users
        2. 若為 General Topic → general_dispatcher 路由（placeholder）
        3. 否則 → 根據 topic_id 找到 instance → send_message

        未授權訊息靜默忽略並記錄 access_denied 事件。
        """
        message = update.effective_message
        if message is None:
            return

        user = update.effective_user
        user_id = user.id if user else 0

        # --- 存取控制 ---
        if not self.is_user_allowed(user_id):
            logger.debug("Access denied for user_id=%d", user_id)
            self.event_logger.log(
                "access_denied",
                instance_name=None,
                data={"user_id": user_id},
            )
            return

        # --- 取得 topic_id ---
        topic_id = getattr(message, "message_thread_id", None)
        general_topic_id = self.config.channel.get("general_topic_id")

        # --- General Topic 路由（placeholder） ---
        if topic_id is not None and topic_id == general_topic_id:
            logger.info(
                "Message from General Topic (topic_id=%d), dispatching...",
                topic_id,
            )
            # TODO: 整合 GeneralDispatcher（Task 9.1）
            return

        # --- Topic → Instance 路由 ---
        if topic_id is not None and topic_id in self.topic_instance_map:
            instance_name = self.topic_instance_map[topic_id]
            text = message.text or ""
            logger.info(
                "Routing message to instance '%s' (topic_id=%d)",
                instance_name,
                topic_id,
            )
            # 透過 fleet_manager 將訊息傳送到 Instance
            if hasattr(self.fleet_manager, "send_message_to_instance"):
                await self.fleet_manager.send_message_to_instance(
                    instance_name, text
                )
            return

        # --- 未映射的 topic，記錄但不處理 ---
        logger.debug(
            "Message from unmapped topic_id=%s, ignoring.", topic_id
        )

    # ------------------------------------------------------------------
    # Inline button 回調
    # ------------------------------------------------------------------

    async def on_callback_query(self, update: Update, context: Any) -> None:
        """處理 inline button 回調（Allow/Deny、重啟/繼續等待/強制停止）。

        callback_data 格式：
        - ``tool_allow:{instance_name}`` — 允許工具使用
        - ``tool_deny:{instance_name}`` — 拒絕工具使用
        - ``hang_restart:{instance_name}`` — 重啟掛起的 Instance
        - ``hang_wait:{instance_name}`` — 繼續等待（忽略掛起警告）
        - ``hang_stop:{instance_name}`` — 強制停止 Instance
        """
        query = update.callback_query
        if query is None:
            return

        # --- 存取控制 ---
        user = query.from_user
        user_id = user.id if user else 0
        if not self.is_user_allowed(user_id):
            logger.debug("Callback access denied for user_id=%d", user_id)
            self.event_logger.log(
                "access_denied",
                instance_name=None,
                data={"user_id": user_id, "source": "callback_query"},
            )
            await query.answer("⛔ 未授權操作")
            return

        # --- 解析 callback_data ---
        data = query.data or ""
        if ":" not in data:
            await query.answer("❌ 無效的回調資料")
            return

        action, instance_name = data.split(":", 1)

        # --- 分派動作 ---
        if action == "tool_allow":
            await self._handle_tool_decision(query, instance_name, allowed=True)
        elif action == "tool_deny":
            await self._handle_tool_decision(query, instance_name, allowed=False)
        elif action == "hang_restart":
            await self._handle_hang_action(query, instance_name, action="restart")
        elif action == "hang_wait":
            await self._handle_hang_action(query, instance_name, action="wait")
        elif action == "hang_stop":
            await self._handle_hang_action(query, instance_name, action="stop")
        else:
            await query.answer("❌ 未知的動作")

    async def _handle_tool_decision(
        self, query: Any, instance_name: str, *, allowed: bool
    ) -> None:
        """處理工具使用 Allow/Deny 決策。"""
        decision = "allow" if allowed else "deny"
        label = "✅ 已允許" if allowed else "❌ 已拒絕"

        if hasattr(self.fleet_manager, "send_tool_decision"):
            await self.fleet_manager.send_tool_decision(instance_name, decision)

        self.event_logger.log(
            "tool_decision",
            instance_name=instance_name,
            data={"decision": decision},
        )

        await query.answer(f"{label} 工具使用")
        await query.edit_message_text(
            f"{label} [{instance_name}] 的工具使用請求"
        )

    async def _handle_hang_action(
        self, query: Any, instance_name: str, *, action: str
    ) -> None:
        """處理掛起偵測的重啟/等待/停止動作。"""
        if action == "restart":
            if hasattr(self.fleet_manager, "restart_instance"):
                await self.fleet_manager.restart_instance(instance_name)
            msg = f"🔄 已重啟 [{instance_name}]"
        elif action == "stop":
            if hasattr(self.fleet_manager, "stop_instance"):
                await self.fleet_manager.stop_instance(instance_name)
            msg = f"⏹ 已停止 [{instance_name}]"
        else:  # wait
            msg = f"⏳ 繼續等待 [{instance_name}]"

        self.event_logger.log(
            "hang_action",
            instance_name=instance_name,
            data={"action": action},
        )

        await query.answer(msg)
        await query.edit_message_text(msg)

    # ------------------------------------------------------------------
    # Inline button 發送輔助
    # ------------------------------------------------------------------

    async def send_inline_buttons(
        self,
        topic_id: int,
        text: str,
        buttons: list[list[tuple[str, str]]],
    ) -> None:
        """發送帶有 InlineKeyboardMarkup 的訊息到指定 Forum Topic。

        Args:
            topic_id: 目標 Forum Topic 的 ID。
            text: 訊息文字。
            buttons: 二維按鈕清單，每個元素為 ``(label, callback_data)``。
                外層 list 為行，內層 list 為同一行的按鈕。
        """
        if self._application is None:
            logger.error("Cannot send inline buttons: Telegram Bot not started")
            return

        group_id = self.config.channel.get("group_id")
        if group_id is None:
            logger.error("Cannot send inline buttons: group_id not configured")
            return

        keyboard = [
            [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
            for row in buttons
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await self._application.bot.send_message(
            chat_id=group_id,
            message_thread_id=topic_id,
            text=text,
            reply_markup=reply_markup,
        )

    # ------------------------------------------------------------------
    # 訊息發送（placeholder — Task 3.3）
    # ------------------------------------------------------------------

    async def send_to_topic(self, topic_id: int, text: str) -> None:
        """發送訊息到指定 Forum Topic，超過 4096 字元自動分割。

        Args:
            topic_id: 目標 Forum Topic 的 ID。
            text: 要發送的文字內容。
        """
        if self._application is None:
            logger.error("Cannot send message: Telegram Bot not started")
            return

        group_id = self.config.channel.get("group_id")
        if group_id is None:
            logger.error("Cannot send message: group_id not configured")
            return

        chunks = split_message(text)
        for chunk in chunks:
            await self._application.bot.send_message(
                chat_id=group_id,
                message_thread_id=topic_id,
                text=chunk,
            )

    # ------------------------------------------------------------------
    # Topic 建立（placeholder — Task 3.3）
    # ------------------------------------------------------------------

    async def create_topic(self, instance_name: str) -> int:
        """在 Telegram Group 中建立新的 Forum Topic。

        Args:
            instance_name: Instance 名稱，作為 Topic 標題。

        Returns:
            新建 Topic 的 ID。
        """
        if self._application is None:
            logger.error("Cannot create topic: Telegram Bot not started")
            return 0

        group_id = self.config.channel.get("group_id")
        if group_id is None:
            logger.error("Cannot create topic: group_id not configured")
            return 0

        result = await self._application.bot.create_forum_topic(
            chat_id=group_id,
            name=instance_name,
        )
        return result.message_thread_id
