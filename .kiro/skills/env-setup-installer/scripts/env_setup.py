#!/usr/bin/env python3
"""ArkBot 環境安裝與驗證腳本

確認並安裝 Python 環境、套件依賴、.env 設定、Gemini API 連通性、Telegram Bot Token。

用法：
    py env_setup.py --path nana_bot --scope full
    py env_setup.py --path nana_bot --scope packages
"""

import argparse
import importlib
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 套件名稱 → 匯入名稱 對照表 ──────────────────────────────
PACKAGE_IMPORT_MAP = {
    "python-telegram-bot": "telegram",
    "google-genai": "google.genai",
    "requests": "requests",
    "beautifulsoup4": "bs4",
    "markdownify": "markdownify",
    "python-dotenv": "dotenv",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "websockets": "websockets",
}

# ── .env 必要欄位 ────────────────────────────────────────────
REQUIRED_ENV_FIELDS = {
    "GOOGLE_API_KEY": "Gemini API 金鑰（從 https://aistudio.google.com/apikey 取得）",
    "TELEGRAM_TOKEN": "Telegram Bot Token（從 @BotFather 取得）",
}
OPTIONAL_ENV_FIELDS = {
    "DATABASE_PATH": ("SQLite 資料庫路徑", "data/brain.db"),
    "WEB_PORT": ("Web 介面埠號", "2141"),
}


def load_env(env_path: Path) -> dict:
    """手動解析 .env 檔案，不依賴 python-dotenv"""
    env = {}
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def parse_requirements(req_path: Path) -> list[str]:
    """解析 requirements.txt，回傳套件名稱列表（不含版本）"""
    packages = []
    if not req_path.exists():
        return packages
    for line in req_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split(">=")[0].split("<=")[0].split("==")[0].split("~=")[0]
        name = name.split("[")[0].strip()
        if name:
            packages.append(name)
    return packages


# ── 結果收集 ────────────────────────────────────────────────
class SetupResult:
    def __init__(self):
        self.stages: list[dict] = []
        self.todos: list[str] = []

    def add_stage(self, name: str, icon: str):
        self.stages.append({"name": name, "icon": icon, "checks": [], "passed": True})

    def add_check(self, name: str, passed: bool, detail: str = ""):
        stage = self.stages[-1]
        stage["checks"].append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            stage["passed"] = False

    def add_todo(self, todo: str):
        self.todos.append(todo)

    def report(self, project_path: str) -> str:
        lines = [
            "🔧 ArkBot 環境安裝與驗證報告",
            "=" * 40,
            f"專案路徑：{project_path}",
            f"執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        total = len(self.stages)
        passed_stages = 0
        for stage in self.stages:
            total_checks = len(stage["checks"])
            passed_checks = sum(1 for c in stage["checks"] if c["passed"])
            if stage["passed"]:
                status = "✅"
                passed_stages += 1
            elif passed_checks > 0:
                status = "⚠️"
            else:
                status = "❌"
            label = f"{stage['icon']} {stage['name']}"
            dots = "." * max(2, 40 - len(label))
            lines.append(f"{label} {dots} {status}（{passed_checks}/{total_checks}）")
            for c in stage["checks"]:
                if not c["passed"]:
                    lines.append(f"   ❌ {c['name']}: {c['detail']}")
            for c in stage["checks"]:
                if c["passed"] and c["detail"]:
                    lines.append(f"   ℹ️  {c['detail']}")

        lines.append("")
        lines.append("=" * 40)
        if passed_stages == total:
            overall = "✅ 全部通過"
        elif passed_stages > 0:
            overall = "⚠️ 部分完成"
        else:
            overall = "❌ 安裝失敗"
        lines.append(f"結果：{overall}（{passed_stages}/{total} 階段通過）")

        if self.todos:
            lines.append("")
            lines.append("📋 待辦事項：")
            for i, todo in enumerate(self.todos, 1):
                lines.append(f"  {i}. {todo}")

        return "\n".join(lines)


# ── 階段 1：Python 環境 ─────────────────────────────────────
def check_python(result: SetupResult):
    result.add_stage("Python 環境", "🐍")

    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    ok = ver >= (3, 9)
    if ok:
        result.add_check("Python 版本 ≥ 3.9", True, f"Python {ver_str}")
    else:
        result.add_check("Python 版本 ≥ 3.9", False, f"Python {ver_str}（需要 ≥ 3.9）")
        result.add_todo("升級 Python：winget install Python.Python.3.12 或從 python.org 下載")

    result.add_check("執行路徑", True, sys.executable)
    result.add_check("平台資訊", True, platform.platform())


# ── 階段 2：套件安裝 ─────────────────────────────────────────
def check_and_install_packages(result: SetupResult, project_path: Path):
    result.add_stage("套件安裝", "📦")

    req_path = project_path / "requirements.txt"
    if not req_path.exists():
        result.add_check("requirements.txt", False, "檔案不存在")
        result.add_todo(f"建立 {project_path}/requirements.txt")
        return

    packages = parse_requirements(req_path)
    if not packages:
        result.add_check("requirements.txt", False, "檔案為空或無法解析")
        return

    # 第一輪：檢查哪些套件缺失
    missing = []
    for pkg in packages:
        import_name = PACKAGE_IMPORT_MAP.get(pkg, pkg)
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pkg)

    # 若有缺失，自動安裝
    if missing:
        result.add_check(
            "缺失套件偵測",
            True,
            f"發現 {len(missing)} 個缺失套件，開始自動安裝...",
        )
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if proc.returncode == 0:
                result.add_check("pip install", True, "自動安裝完成")
            else:
                err = proc.stderr.strip()[-200:] if proc.stderr else "未知錯誤"
                result.add_check("pip install", False, f"安裝失敗：{err}")
                result.add_todo(f"手動安裝：py -m pip install -r {req_path}")
        except subprocess.TimeoutExpired:
            result.add_check("pip install", False, "安裝逾時（120 秒）")
            result.add_todo(f"手動安裝：py -m pip install -r {req_path}")
        except Exception as e:
            result.add_check("pip install", False, str(e))
            result.add_todo(f"手動安裝：py -m pip install -r {req_path}")

    # 第二輪：重新驗證所有套件
    all_ok = True
    for pkg in packages:
        import_name = PACKAGE_IMPORT_MAP.get(pkg, pkg)
        try:
            # 清除匯入快取以偵測新安裝的套件
            if import_name in sys.modules:
                del sys.modules[import_name]
            importlib.import_module(import_name)
            result.add_check(pkg, True)
        except ImportError as e:
            result.add_check(pkg, False, f"無法匯入 {import_name}：{e}")
            all_ok = False

    if not missing:
        result.add_check("套件狀態", True, f"全部 {len(packages)} 個套件已就緒")
    elif all_ok:
        result.add_check("套件狀態", True, f"已自動安裝 {len(missing)} 個缺失套件，全部就緒")


# ── 階段 3：.env 環境變數 ───────────────────────────────────
def check_and_setup_env(result: SetupResult, project_path: Path):
    result.add_stage("環境變數", "📝")

    env_path = project_path / ".env"
    example_path = project_path / ".env.example"

    # 若 .env 不存在，嘗試從 .env.example 複製
    if not env_path.exists():
        if example_path.exists():
            shutil.copy2(example_path, env_path)
            result.add_check(".env 檔案", True, "已從 .env.example 複製建立")
        else:
            result.add_check(".env 檔案", False, ".env 與 .env.example 都不存在")
            result.add_todo(f"在 {project_path}/ 建立 .env 檔案，設定 GOOGLE_API_KEY 和 TELEGRAM_TOKEN")
            return
    else:
        result.add_check(".env 檔案", True, "已存在")

    env = load_env(env_path)

    # 檢查必要欄位
    for field, desc in REQUIRED_ENV_FIELDS.items():
        value = env.get(field, "")
        if value and not value.startswith("your-"):
            result.add_check(field, True, "已設定")
        else:
            result.add_check(field, False, f"未設定（{desc}）")
            result.add_todo(f"編輯 {env_path}，填入 {field}")

    # 檢查選用欄位
    for field, (desc, default) in OPTIONAL_ENV_FIELDS.items():
        value = env.get(field, "")
        if value:
            result.add_check(field, True, value)
        else:
            result.add_check(field, True, f"使用預設值：{default}")


# ── 階段 4：Gemini API ──────────────────────────────────────
def check_gemini(result: SetupResult, project_path: Path):
    result.add_stage("Gemini API", "🤖")

    env = load_env(project_path / ".env")
    api_key = env.get("GOOGLE_API_KEY", "")

    if not api_key or api_key.startswith("your-"):
        result.add_check("GOOGLE_API_KEY", False, "未設定或為預設值")
        result.add_todo("設定 GOOGLE_API_KEY 後重新執行：py env_setup.py --path <路徑> --scope gemini")
        return

    result.add_check("GOOGLE_API_KEY", True, "已設定")

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        result.add_check("Client 初始化", True)
    except ImportError:
        result.add_check("Client 初始化", False, "google-genai 套件未安裝")
        return
    except Exception as e:
        result.add_check("Client 初始化", False, str(e))
        result.add_todo("檢查 GOOGLE_API_KEY 是否正確：https://aistudio.google.com/apikey")
        return

    try:
        models_response = client.models.list()
        model_names = []
        for m in models_response:
            name = m.name if hasattr(m, "name") else str(m)
            if "gemini" in name.lower():
                model_names.append(name)

        if model_names:
            result.add_check("可用模型", True, f"找到 {len(model_names)} 個 Gemini 模型")
            for name in model_names[:10]:
                result.add_check(f"  {name}", True)
            if len(model_names) > 10:
                result.add_check(f"  ...還有 {len(model_names) - 10} 個", True)
        else:
            result.add_check("可用模型", False, "未找到任何 Gemini 模型")
    except Exception as e:
        result.add_check("模型清單", False, str(e))
        result.add_todo("檢查網路連線或代理設定（HTTPS_PROXY）")


# ── 階段 5：Telegram Bot Token ──────────────────────────────
def check_telegram(result: SetupResult, project_path: Path):
    result.add_stage("Telegram Bot Token", "💬")

    env = load_env(project_path / ".env")
    token = env.get("TELEGRAM_TOKEN", "")

    if not token or token.startswith("your-"):
        result.add_check("TELEGRAM_TOKEN", False, "未設定或為預設值")
        result.add_todo("設定 TELEGRAM_TOKEN 後重新執行：py env_setup.py --path <路徑> --scope telegram")
        return

    result.add_check("TELEGRAM_TOKEN", True, "已設定")

    try:
        import requests
        proxies = {}
        https_proxy = env.get("HTTPS_PROXY", "")
        if https_proxy:
            proxies = {"https": https_proxy, "http": https_proxy}

        url = f"https://api.telegram.org/bot{token}/getMe"
        resp = requests.get(url, timeout=10, proxies=proxies if proxies else None)
        data = resp.json()

        if resp.status_code == 200 and data.get("ok"):
            bot = data["result"]
            username = bot.get("username", "N/A")
            first_name = bot.get("first_name", "N/A")
            bot_id = bot.get("id", "N/A")
            result.add_check("Token 有效", True, f"@{username}（{first_name}，ID: {bot_id}）")
        else:
            desc = data.get("description", resp.text[:100])
            result.add_check("Token 有效", False, f"API 回應：{desc}")
            result.add_todo("從 @BotFather 重新取得 Token")
    except ImportError:
        result.add_check("Token 有效", False, "requests 套件未安裝")
    except Exception as e:
        err_msg = str(e)
        if "ConnectionError" in err_msg or "ProxyError" in err_msg:
            result.add_check("Token 有效", False, "無法連線到 Telegram API（檢查網路或代理設定）")
            result.add_todo("設定 HTTPS_PROXY 或檢查網路連線")
        else:
            result.add_check("Token 有效", False, err_msg)


# ── 主程式 ──────────────────────────────────────────────────
SCOPE_STAGES = {
    "python": ["python"],
    "packages": ["python", "packages"],
    "env": ["python", "packages", "env"],
    "gemini": ["python", "packages", "env", "gemini"],
    "telegram": ["python", "packages", "env", "telegram"],
    "full": ["python", "packages", "env", "gemini", "telegram"],
}


def run(project_path: str, scope: str = "full") -> str:
    """執行環境安裝與驗證，回傳報告字串"""
    path = Path(project_path)
    if not path.exists():
        return f"❌ 專案路徑不存在：{project_path}"
    if not path.is_dir():
        return f"❌ 路徑不是目錄：{project_path}"

    stages = SCOPE_STAGES.get(scope, SCOPE_STAGES["full"])
    result = SetupResult()

    if "python" in stages:
        check_python(result)
    if "packages" in stages:
        check_and_install_packages(result, path)
    if "env" in stages:
        check_and_setup_env(result, path)
    if "gemini" in stages:
        check_gemini(result, path)
    if "telegram" in stages:
        check_telegram(result, path)

    return result.report(project_path)


def main():
    parser = argparse.ArgumentParser(description="ArkBot 環境安裝與驗證")
    parser.add_argument("--path", required=True, help="ArkBot 專案根目錄路徑")
    parser.add_argument(
        "--scope",
        default="full",
        choices=["python", "packages", "env", "gemini", "telegram", "full"],
        help="安裝範圍（預設：full）",
    )
    args = parser.parse_args()
    print(run(args.path, args.scope))


if __name__ == "__main__":
    main()
