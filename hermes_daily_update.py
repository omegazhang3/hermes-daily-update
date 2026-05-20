#!/usr/bin/env python3
"""Hermes Agent 每日自动更新脚本 (Linux cron 模式)
- 始终执行 hermes update（代码 + 依赖 + gateway 重启）
- 比较版本变化
- 可选：Telegram 通知（配置了凭证才发送，未配置则静默跳过）
- 无更新时静默退出
"""

import subprocess
import os
import json
import urllib.request

REPO_DIR = "/home/hermes/hermes-agent"

# 确保 cron 环境也能找到 hermes
os.environ["PATH"] = "/home/hermes/.local/bin" + ":" + os.environ.get("PATH", "")

# Telegram 配置（可选，从 .env 读取）
def load_env():
    env = {}
    env_path = "/home/hermes/aimint/hermes-daily-update/.env"
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
    out, rc = run("hermes --version")
    if rc == 0 and out:
        for part in out.split("\n"):
            if "Hermes" in part or "v0." in part:
                return part.strip()
        return out.split("\n")[0].strip()

    hermes_bin = "/home/hermes/.local/bin/hermes"
    if os.path.exists(hermes_bin):
        out, rc = run(f"{hermes_bin} --version")
        if rc == 0 and out:
            for part in out.split("\n"):
                if "Hermes" in part or "v0." in part:
                    return part.strip()

    pkg_json = os.path.join(REPO_DIR, "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                return f"v{pkg.get('version', '?')}"
        except:
            pass

    out, rc = run("git describe --tags --abbrev=0 2>/dev/null", cwd=REPO_DIR)
    if rc == 0 and out:
        return out.strip()

    return "unknown"

def send_telegram(text):
    """发送 Telegram 通知，凭证未配置则静默跳过"""
    if not BOT_TOKEN or not CHAT_ID:
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

    # 2. 记录 git pull 前的 HEAD，用于后续对比
    run("git fetch origin", cwd=REPO_DIR)
    old_head, _ = run("git rev-parse HEAD", cwd=REPO_DIR)
    pull_out, _ = run("git pull origin main", cwd=REPO_DIR)
    new_head, _ = run("git rev-parse HEAD", cwd=REPO_DIR)
    git_updated = (old_head != new_head)

    # 3. 始终执行 hermes update（核心：确保依赖和 gateway 最新）
    subprocess.run("hermes update", shell=True)

    # 4. 判断是否有实际更新
    if not git_updated and "Already up to date" in pull_out:
        print("No updates available.")
        return

    # 5. 有更新 → 获取新版本
    version_after = get_version()

    # 6. 统计更新的 commit 数
    log_out, _ = run(f"git log --oneline {old_head}..{new_head} 2>/dev/null | wc -l", cwd=REPO_DIR)
    commit_count = log_out.strip() if log_out.strip().isdigit() else "?"

    # 7. 获取新功能列表
    changelog_out, _ = run(f"git log --oneline {old_head}..{new_head} 2>/dev/null", cwd=REPO_DIR)
    commits = []
    if changelog_out:
        for line in changelog_out.strip().split("\n"):
            line = line.strip()
            if line:
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    commits.append(parts[1])

    skip_keywords = ["merge", "typo", "format", "whitespace", "bump version", "chore:"]
    features = [f"  • {c}" for c in commits if not any(kw in c.lower() for kw in skip_keywords)]

    features_text = "\n".join(features[:10]) if features else "  (无详细描述)"
    if len(features) > 10:
        features_text += f"\n  ... 还有 {len(features) - 10} 项"

    # 8. 发送 Telegram 通知（可选）
    report = f"""🔄 Hermes 每日更新

📦 版本: {version_after}
📋 更新前: {version_before}
新 commits: {commit_count}

📝 更新内容:
{features_text}"""

    send_telegram(report)
    print(report)

if __name__ == "__main__":
    main()
