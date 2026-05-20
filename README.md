[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent daily auto-update script with Telegram notifications.

## Features

- `hermes update` to update Hermes Agent (code + dependencies + gateway restart)
- Detect version changes
- Display new version number prominently
- Show changelog (filtered commit messages, skips merge/typo/chore)
- Send Telegram notification with update details
- Auto-restart gateway after update
- Silent exit when no updates available
- **Robust version detection**: tries `hermes --version`, full path, package.json, git tags

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
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
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

## Why Linux Crontab?

Hermes cron scheduler may miss job triggers if the gateway restarts near the scheduled time. Linux crontab runs independently of the gateway process, making it more reliable for time-critical daily updates.

## Why `.env` in Project Directory?

In cron environments, the `HOME` variable may be overridden (e.g. set to `~/.hermes` instead of `~`), which causes `os.path.expanduser("~/.hermes/.env")` to resolve to an incorrect path like `~/.hermes/.hermes/.env`. To avoid this issue, the script reads credentials from `.env` in the project directory using an absolute path. This is more reliable and keeps credentials isolated per project.

## License

MIT
