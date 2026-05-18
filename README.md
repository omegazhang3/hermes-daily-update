[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent daily auto-update script with Telegram notifications.

## Features

- `git pull` to update Hermes Agent code
- Detect version changes
- Display new version number prominently
- Show changelog (filtered commit messages, skips merge/typo/chore)
- Send Telegram notification with update details
- Auto-restart gateway after update
- Silent exit when no updates available

## Notification Example

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

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Telegram credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   HERMES_REPO_DIR=/home/hermes/hermes-agent
   ```

## Usage

```bash
python3 hermes_daily_update.py
```

### Linux Crontab (recommended)

```bash
# Beijing time 01:05 (UTC 17:05)
5 17 * * * /usr/bin/python3 /path/to/hermes_daily_update.py >> /path/to/logs/daily_update.log 2>&1
```

### Hermes Cron (alternative)

```bash
hermes cron add --name "hermes-daily-update" --schedule "5 19 * * *" --script hermes_daily_update.py --deliver telegram:your_chat_id
```

## Why Linux Crontab?

Hermes cron scheduler may miss job triggers if the gateway restarts near the scheduled time. Linux crontab runs independently of the gateway process, making it more reliable for time-critical daily updates.

## License

MIT
