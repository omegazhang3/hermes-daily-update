[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent 每日自动更新脚本，通过 Telegram 通知更新结果。

## 功能

- `git pull` 更新 Hermes Agent 代码
- 检测版本变化
- 显示新版本号
- 显示更新内容（过滤后的 commit 信息，跳过 merge/typo/chore）
- 发送 Telegram 通知（包含版本号、更新内容）
- 自动重启 gateway
- 无更新时静默退出

## 通知示例

```
🔄 Hermes 每日更新

📦 版本: Hermes v0.14.x
📋 更新前: Hermes v0.13.x
新 commits: 147

📝 更新内容:
  • feat(browser): browser-use + firecrawl plugins
  • feat(xai): add xAI Grok OAuth provider
  • feat(cli): add `hermes send` to pipe script output
  • feat(status): append session recap to /status output
  • feat(cli): show ▶ N indicator for background tasks
  • feat(cli): add /exit --delete flag
  • feat(agent): Added gemma 4 to reasoning allowlist
  • feat(tools): mirror image_gen plugin-injection
  • feat(gateway): add .ts/.py/.sh to SUPPORTED_DOCUMENT_TYPES
  • feat(discord): allow_any_attachment config
  ... 还有 137 项

正在重启 gateway...
```

## 配置

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 填入你的配置：
   ```
   TELEGRAM_BOT_TOKEN=你的Bot Token
   TELEGRAM_CHAT_ID=你的Chat ID
   HERMES_REPO_DIR=/home/hermes/hermes-agent
   ```

## 使用

```bash
python3 hermes_daily_update.py
```

### Linux Crontab（推荐）

```bash
# 北京时间 01:05（UTC 17:05）
5 17 * * * /usr/bin/python3 /path/to/hermes_daily_update.py >> /path/to/logs/daily_update.log 2>&1
```

### Hermes Cron（备选）

```bash
hermes cron add --name "hermes-daily-update" --schedule "5 19 * * *" --script hermes_daily_update.py --deliver telegram:your_chat_id
```

## 为什么用 Linux Crontab？

Hermes cron 调度器在 gateway 重启时可能错过触发窗口。Linux crontab 独立于 gateway 运行，对时间敏感的每日更新更可靠。

## License

MIT
