#!/usr/bin/env python3
"""Hermes Agent 每日自动更新脚本
- git pull 更新代码
- 比较版本变化
- 发送 Telegram 通知
- 重启 gateway（如有更新）
"""

import subprocess
import os
import sys
from pathlib import Path

# 从脚本同目录的 .env 文件加载配置
def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

load_env()

REPO_DIR = os.environ.get("HERMES_REPO_DIR", "/home/hermes/hermes-agent")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def run(cmd, cwd=None):
    """运行命令，返回 (stdout, returncode)"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=cwd)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "timeout", 1

def get_version():
    out, rc = run("hermes --version")
    if rc == 0:
        for part in out.split("\n"):
            if "Hermes" in part or "v0." in part:
                return part.strip()
    return out or "unknown"

def send_telegram(text):
    """通过 curl 发送 Telegram 消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification")
        return

    import urllib.request
    import json
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram notification failed: {e}")

def main():
    # 1. 更新前版本
    version_before = get_version()
    
    # 2. git fetch + pull
    run("git fetch origin", cwd=REPO_DIR)
    pull_out, pull_rc = run("git pull origin main", cwd=REPO_DIR)
    
    # 3. 检查是否有更新
    if "Already up to date" in pull_out or "已经是最新的" in pull_out:
        print("Already up to date, no notification needed.")
        return
    
    # 4. 有更新，获取新版本
    version_after = get_version()
    
    # 5. 统计更新的 commit 数
    log_out, _ = run("git log --oneline HEAD@{1}..HEAD 2>/dev/null | wc -l", cwd=REPO_DIR)
    commit_count = log_out.strip() if log_out.strip().isdigit() else "?"
    
    # 6. 构建报告
    report = f"""🔄 Hermes 每日更新

更新前: {version_before}
更新后: {version_after}
新 commits: {commit_count}
状态: ✅ 更新成功

正在重启 gateway..."""
    
    print(report)
    send_telegram(report)
    
    # 7. 重启 gateway（更新后才重启）
    import time
    time.sleep(2)
    run("systemctl --user restart hermes-gateway")

if __name__ == "__main__":
    main()
