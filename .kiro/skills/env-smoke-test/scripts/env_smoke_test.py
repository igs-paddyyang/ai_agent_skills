#!/usr/bin/env python3
"""ArkBot 環境煙霧測試腳本

驗證 Python 版本、套件安裝、Gemini API 連通性、Telegram Bot Token 有效性。

用法：
    py env_smoke_test.py --path nana_bot --scope all
"""

import argparse
import importlib
import json
import os
import platform
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
        # 移除版本限制與 extras（如 uvicorn[standard]>=0.27.0）
        name = line.split(">=")[0].split("<=")[0].split("==")[0].split("~=")[0]
        name = name.split("[")[0].strip()
        if name:
            packages.append(name)
    return packages


# ── 結果收集 ────────────────────────────────────────────────
class TestResult:
    def __init__(self):
        self.stages: list[dict] = []

    def add_stage(self, name: str, icon: str):
        self.stages.append({"name": name, "icon": icon, "checks": [], "passed": True})

    def add_check(self, name: str, passed: bool, detail: str = ""):
        stage = self.stages[-1]
        stage["checks"].append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            stage["passed"] = False

    def report(self, project_path: str) -> str:
        lines = [
            "🧪 ArkBot 環境煙霧測試報告",
            "=" * 40,
            f"專案路徑：{project_path}",
            f"測試時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        total = len(self.stages)
        passed_stages = 0
        for stage in self.stages:
            total_checks = len(stage["checks"])
            passed_checks = sum(1 for c in stage["checks"] if c["passed"])
            status = "✅" if stage["passed"] else "❌"
            if stage["passed"]:
                passed_stages += 1
            label = f"{stage['icon']} {stage['name']}"
            dots = "." * max(2, 40 - len(label))
            lines.append(f"{label} {dots} {status} （{passed_checks}/{total_checks}）")
            # 顯示失敗項目的詳情
            for c in stage["checks"]:
                if not c["passed"]:
                    lines.append(f"   ❌ {c['name']}: {c['detail']}")
            # 顯示額外資訊（通過的項目若有 detail 也顯示）
            for c in stage["checks"]:
                if c["passed"] and c["detail"]:
                    lines.append(f"   ℹ️  {c['detail']}")

        lines.append("")
        lines.append("=" * 40)
        overall = "✅ 全部通過" if passed_stages == total else "❌ 有失敗項目"
        lines.append(f"結果：{overall}（{passed_stages}/{total} 階段）")
        return "\n".join(lines)


# ── 階段 1：Python 環境 ─────────────────────────────────────
def check_python(result: TestResult):
    result.add_stage("Python 環境", "🐍")

    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    ok = ver >= (3, 9)
    result.add_check(
        "Python 版本 ≥ 3.9",
        ok,
        f"Python {ver_str}" if ok else f"Python {ver_str}（需要 ≥ 3.9）",
    )
    result.add_check("執行路徑", True, sys.executable)
    result.add_check("平台資訊", True, platform.platform())


# ── 階段 2：套件安裝 ─────────────────────────────────────────
def check_packages(result: TestResult, project_path: Path):
    result.add_stage("套件安裝", "📦")

    req_path = project_path / "requirements.txt"
    if not req_path.exists():
        result.add_check("requirements.txt", False, "檔案不存在")
        return

    packages = parse_requirements(req_path)
    if not packages:
        result.add_check("requirements.txt", False, "檔案為空或無法解析")
        return

    for pkg in packages:
        import_name = PACKAGE_IMPORT_MAP.get(pkg, pkg)
        try:
            importlib.import_module(import_name)
            result.add_check(pkg, True)
        except ImportError as e:
            result.add_check(pkg, False, f"無法匯入 {import_name}：{e}")


# ── 階段 3：Gemini API ──────────────────────────────────────
def check_gemini(result: TestResult, project_path: Path):
    result.add_stage("Gemini API", "🤖")

    env = load_env(project_path / ".env")
    api_key = env.get("GOOGLE_API_KEY", "")

    if not api_key or api_key.startswith("your-"):
        result.add_check("GOOGLE_API_KEY", False, "未設定或為預設值")
        return

    result.add_check("GOOGLE_API_KEY", True, "已設定")

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        result.add_check("Client 初始化", True)
    except Exception as e:
        result.add_check("Client 初始化", False, str(e))
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
            # 列出前 10 個模型
            display = model_names[:10]
            for name in display:
                result.add_check(f"  {name}", True)
            if len(model_names) > 10:
                result.add_check(f"  ...還有 {len(model_names) - 10} 個", True)
        else:
            result.add_check("可用模型", False, "未找到任何 Gemini 模型")
    except Exception as e:
        result.add_check("模型清單", False, str(e))


# ── 階段 4：Telegram Bot Token ──────────────────────────────
def check_telegram(result: TestResult, project_path: Path):
    result.add_stage("Telegram Bot Token", "🤖")

    env = load_env(project_path / ".env")
    token = env.get("TELEGRAM_TOKEN", "")

    if not token or token.startswith("your-"):
        result.add_check("TELEGRAM_TOKEN", False, "未設定或為預設值")
        return

    result.add_check("TELEGRAM_TOKEN", True, "已設定")

    try:
        import requests
        # 支援代理
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
    except requests.exceptions.ConnectionError:
        result.add_check("Token 有效", False, "無法連線到 Telegram API（檢查網路或代理設定）")
    except Exception as e:
        result.add_check("Token 有效", False, str(e))


# ── 主程式 ──────────────────────────────────────────────────
SCOPE_STAGES = {
    "python": ["python"],
    "packages": ["python", "packages"],
    "gemini": ["python", "packages", "gemini"],
    "telegram": ["python", "packages", "telegram"],
    "all": ["python", "packages", "gemini", "telegram"],
}


def run(project_path: str, scope: str = "all") -> str:
    """執行環境煙霧測試，回傳報告字串"""
    path = Path(project_path)
    if not path.exists():
        return f"❌ 專案路徑不存在：{project_path}"
    if not path.is_dir():
        return f"❌ 路徑不是目錄：{project_path}"

    stages = SCOPE_STAGES.get(scope, SCOPE_STAGES["all"])
    result = TestResult()

    if "python" in stages:
        check_python(result)
    if "packages" in stages:
        check_packages(result, path)
    if "gemini" in stages:
        check_gemini(result, path)
    if "telegram" in stages:
        check_telegram(result, path)

    return result.report(project_path)


def main():
    parser = argparse.ArgumentParser(description="ArkBot 環境煙霧測試")
    parser.add_argument("--path", required=True, help="ArkBot 專案根目錄路徑")
    parser.add_argument(
        "--scope",
        default="all",
        choices=["python", "packages", "gemini", "telegram", "all"],
        help="測試範圍（預設：all）",
    )
    args = parser.parse_args()
    print(run(args.path, args.scope))


if __name__ == "__main__":
    main()
