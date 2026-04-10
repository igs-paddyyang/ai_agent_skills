"""kiro-agent — 多 Agent 艦隊管理系統

將 Telegram 轉變為 AI 編碼 Agent 的指揮中心，
以 Kiro CLI 為主要後端，支援多種 AI CLI 後端混用。
"""

from pathlib import Path

__version__ = "0.1.0"

# 執行時資料目錄
RUNTIME_DIR = Path.home() / ".kiro-agent"

# 子目錄結構
RUNTIME_SUBDIRS = [
    RUNTIME_DIR / "instances",
]


def ensure_runtime_dirs() -> Path:
    """確保 ~/.kiro-agent/ 及其子目錄存在。

    Returns:
        RUNTIME_DIR 的 Path 物件
    """
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in RUNTIME_SUBDIRS:
        subdir.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR
