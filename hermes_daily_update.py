#!/usr/bin/env python3
"""Hermes Agent 每日自动更新脚本 (Linux cron 模式)
- git pull 更新代码
- 比较版本变化
- 直接通过 Telegram Bot API 发送通知
- 重启 gateway（如有更新）
- 无更新时静默退出
"""

import subprocess
import os
import time
import json
import urllib.request

REPO_DIR = "/home/hermes/hermes-agent"

# 确保 cron 环境也能找到 hermes
os.environ["PATH"] = os.path.expanduser("~/.local/bin") + ":" + os.environ.get("PATH", "")

# Telegram 配置（从 .env 读取）
def load_env():
    env = {}
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

_env = load_env()
BOT_TOKEN = _env.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = _env.get("TELEGRAM_CHAT_ID", _env.get("TELEGRAM_HOME_CHANNEL", ""))

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=cwd)
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "timeout", 1

def get_version():
    """获取 Hermes 版本，多种方式尝试"""
    # 方式1: hermes --version
    out, rc = run("hermes --version")
    if rc == 0 and out:
        for part in out.split("\n"):
            if "Hermes" in part or "v0." in part:
                return part.strip()
        # 返回第一行
        return out.split("\n")[0].strip()
    
    # 方式2: 尝试完整路径
    hermes_bin = os.path.expanduser("~/.local/bin/hermes")
    if os.path.exists(hermes_bin):
        out, rc = run(f"{hermes_bin} --version")
        if rc == 0 and out:
            for part in out.split("\n"):
                if "Hermes" in part or "v0." in part:
                    return part.strip()
    
    # 方式3: 从 package.json 读取版本
    pkg_json = os.path.join(REPO_DIR, "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                return f"v{pkg.get('version', '?')}"
        except:
            pass
    
    # 方式4: 从 git tag 获取
    out, rc = run("git describe --tags --abbrev=0 2>/dev/null", cwd=REPO_DIR)
    if rc == 0 and out:
        return out.strip()
    
    return "unknown"

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Warning: Telegram credentials not found")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"Telegram send failed: {e}")

def main():
    # 1. 更新前版本
    version_before = get_version()

    # 2. git fetch + pull
    run("git fetch origin", cwd=REPO_DIR)
    pull_out, pull_rc = run("git pull origin main", cwd=REPO_DIR)

    # 3. 无更新 → 静默退出
    if "Already up to date" in pull_out or "已经是最新的" in pull_out:
        return

    # 3.5 更新 Hermes CLI
    subprocess.run("hermes update", shell=True, timeout=120)

    # 4. 有更新 → 获取新版本
    version_after = get_version()

    # 5. 统计更新的 commit 数
    log_out, _ = run("git log --oneline HEAD@{1}..HEAD 2>/dev/null | wc -l", cwd=REPO_DIR)
    commit_count = log_out.strip() if log_out.strip().isdigit() else "?"

    # 6. 获取新功能列表（最近 commit 信息）
    changelog_out, _ = run("git log --oneline HEAD@{1}..HEAD 2>/dev/null", cwd=REPO_DIR)
    commits = []
    if changelog_out:
        for line in changelog_out.strip().split("\n"):
            line = line.strip()
            if line:
                # 去掉 commit hash，只保留描述
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    commits.append(parts[1])

    # 过滤出有价值的功能 commit（跳过 merge/fix typo 等）
    features = []
    skip_keywords = ["merge", "typo", "format", "whitespace", "bump version", "chore:"]
    for c in commits:
        if not any(kw in c.lower() for kw in skip_keywords):
            features.append(f"  • {c}")

    features_text = "\n".join(features[:10]) if features else "  (无详细描述)"
    if len(features) > 10:
        features_text += f"\n  ... 还有 {len(features) - 10} 项"

    # 7. 发送 Telegram 通知
    report = f"""🔄 Hermes 每日更新

📦 版本: {version_after}
📋 更新前: {version_before}
新 commits: {commit_count}

📝 更新内容:
{features_text}

正在重启 gateway..."""
    
    send_telegram(report)
    print(report)

    # 7. 等消息发出后重启 gateway
    time.sleep(3)
    run("systemctl --user restart hermes-gateway")

if __name__ == "__main__":
    main()
