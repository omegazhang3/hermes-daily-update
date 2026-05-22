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
import re
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
    """获取 Hermes 版本，优先读取仓库内真实版本来源（git pull 后会变化），
    避免 `hermes --version` 返回 CLI 自身版本导致 before/after 相同。"""
    # 1) 仓库内 package.json + 当前 commit（最准确反映 git pull 后的变化）
    pkg_json = os.path.join(REPO_DIR, "package.json")
    pkg_version = None
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
                v = pkg.get("version")
                if v:
                    pkg_version = f"v{v}"
        except Exception:
            pass

    short_sha, rc = run("git rev-parse --short HEAD", cwd=REPO_DIR)
    if rc == 0 and short_sha:
        if pkg_version:
            return f"{pkg_version} ({short_sha})"
        return short_sha

    if pkg_version:
        return pkg_version

    # 2) 仓库最近 tag
    out, rc = run("git describe --tags --abbrev=0 2>/dev/null", cwd=REPO_DIR)
    if rc == 0 and out:
        return out.strip()

    # 3) 兜底：hermes CLI 版本
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

    return "unknown"

CATEGORY_LABELS = [
    ("feat",     "✨ 新功能"),
    ("fix",      "🐛 Bug 修复"),
    ("perf",     "⚡ 性能优化"),
    ("refactor", "♻️  重构"),
    ("security", "🔒 安全更新"),
    ("docs",     "📚 文档"),
]
SKIP_TYPES = {"chore", "style", "test", "ci", "build", "merge"}
SKIP_KEYWORDS = ["typo", "format", "whitespace", "bump version"]

def _clean_subject(subject):
    """美化单条 commit subject：去前缀、去 issue 号、首字母大写。"""
    s = subject.strip()
    s = re.sub(r"\s*\(#\d+\)\s*$", "", s)         # 去掉末尾 (#123)
    s = re.sub(r"\s*#\d+\s*$", "", s)             # 去掉末尾 #123
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    if s:
        s = s[0].upper() + s[1:]
    return s

def _parse_commit(subject):
    """解析 Conventional Commit，返回 (type, clean_subject) 或 (None, clean_subject)。"""
    m = re.match(r"^([a-zA-Z]+)(?:\([^)]*\))?!?:\s*(.+)$", subject)
    if m:
        return m.group(1).lower(), _clean_subject(m.group(2))
    return None, _clean_subject(subject)

def format_changelog(changelog_out):
    """把 `git log --oneline` 输出格式化成分组、易读的更新内容。"""
    if not changelog_out or not changelog_out.strip():
        return "  (无详细描述)"

    groups = {key: [] for key, _ in CATEGORY_LABELS}
    others = []

    for line in changelog_out.strip().split("\n"):
        parts = line.strip().split(" ", 1)
        if len(parts) < 2:
            continue
        subject = parts[1]
        lower = subject.lower()
        if any(kw in lower for kw in SKIP_KEYWORDS):
            continue

        ctype, clean = _parse_commit(subject)
        if ctype in SKIP_TYPES:
            continue
        if not clean:
            continue

        if ctype in groups:
            groups[ctype].append(clean)
        else:
            others.append(clean)

    sections = []
    for key, label in CATEGORY_LABELS:
        items = groups[key]
        if not items:
            continue
        shown = items[:8]
        block = [label + ":"] + [f"  • {x}" for x in shown]
        if len(items) > 8:
            block.append(f"  ... 还有 {len(items) - 8} 项")
        sections.append("\n".join(block))

    if others:
        shown = others[:8]
        block = ["📌 其他:"] + [f"  • {x}" for x in shown]
        if len(others) > 8:
            block.append(f"  ... 还有 {len(others) - 8} 项")
        sections.append("\n".join(block))

    return "\n\n".join(sections) if sections else "  (无值得汇报的变更)"

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

    # 6. 获取新功能列表（解析 Conventional Commits，分组易读）
    changelog_out, _ = run(f"git log --oneline {old_head}..{new_head} 2>/dev/null", cwd=REPO_DIR)
    features_text = format_changelog(changelog_out)

    # 7. 发送 Telegram 通知（可选）
    report = f"""🔄 Hermes 每日更新

📦 版本: {version_after}
📋 更新前: {version_before}

📝 更新内容:
{features_text}"""

    send_telegram(report)
    print(report)

if __name__ == "__main__":
    main()
