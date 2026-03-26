"""Notify Core — TG 發送核心（設定載入 + 路由解析 + 訊息發送）

格式化邏輯在 skills/notify/assets/tg_formatter.py
本模組只負責：載入 telegram.json → 解析路由 → 發送訊息
"""
import json
import os
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

CONFIG_PATH = PROJECT_ROOT / "config" / "telegram.json"


def load_config() -> dict:
    """載入 telegram.json 設定"""
    if not CONFIG_PATH.exists():
        logger.error(f"設定檔不存在：{CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f).get("telegram", {})


def get_bot_token(cfg: dict) -> str:
    """取得 bot token（支援 ${ENV_VAR} 替換）"""
    token = cfg.get("bot_token", "")
    if token.startswith("${") and token.endswith("}"):
        env_key = token[2:-1]
        return os.getenv(env_key, "")
    return token


def resolve_targets(cfg: dict, route_name: str) -> list[dict]:
    """解析 notify_routes 中的 targets 為實際的 chat_id + message_thread_id"""
    routes = cfg.get("notify_routes", {})
    route = routes.get(route_name, {})
    targets_cfg = route.get("targets", [])

    admin_chat_id = cfg.get("admin", {}).get("chat_id", "")
    group_chat_id = cfg.get("group", {}).get("chat_id", "")
    topics = cfg.get("group", {}).get("topics", {})
    additional = cfg.get("additional_groups", {})

    targets = []
    for t in targets_cfg:
        ttype = t.get("type")
        if ttype == "admin" and admin_chat_id:
            targets.append({"chat_id": admin_chat_id})
        elif ttype == "topic":
            topic_name = t.get("topic", "")
            thread_id = topics.get(topic_name)
            if group_chat_id and thread_id is not None:
                entry = {"chat_id": group_chat_id}
                if thread_id > 0:
                    entry["message_thread_id"] = thread_id
                targets.append(entry)
        elif ttype == "group":
            group_key = t.get("group", "")
            grp = additional.get(group_key, {})
            if grp.get("enabled", True) and grp.get("chat_id"):
                targets.append({"chat_id": grp["chat_id"]})
    return targets


def send_telegram(token: str, chat_id: str, text: str,
                  parse_mode: str = "Markdown",
                  message_thread_id: int | None = None) -> bool:
    """透過 Telegram Bot API 發送訊息"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    proxies = {"https": proxy} if proxy else None
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if message_thread_id:
        payload["message_thread_id"] = message_thread_id
    try:
        resp = requests.post(url, json=payload, proxies=proxies, timeout=15)
        if resp.status_code == 200:
            logger.info(f"TG 通報成功 -> chat_id={chat_id}, thread={message_thread_id}")
            return True
        else:
            logger.error(f"TG 通報失敗：{resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"TG 通報例外：{e}")
        return False


def send_to_route(message: str, route: str = "default") -> str:
    """發送訊息到指定路由，回傳結果摘要"""
    cfg = load_config()
    token = get_bot_token(cfg)

    if not token:
        return f"[PREVIEW] bot_token 未設定\n\n{message}"

    targets = resolve_targets(cfg, route)
    if not targets:
        return f"[PREVIEW] 路由 '{route}' 無有效目標\n\n{message}"

    # 不使用 Markdown parse_mode（避免 emoji + 特殊字元解析錯誤）
    results = []
    for t in targets:
        ok = send_telegram(
            token, t["chat_id"], message,
            parse_mode=None,
            message_thread_id=t.get("message_thread_id"),
        )
        results.append(f"  {'[OK]' if ok else '[FAIL]'} chat_id={t['chat_id']}")

    return f"通報完成（{len(targets)} 個目標）：\n" + "\n".join(results)
