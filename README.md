[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent daily auto-update script with optional Telegram notifications.

## Features

- **Always runs `hermes update`** — ensures code, dependencies, and gateway are up to date
- Reliable version detection — reads `package.json` + commit SHA from the agent repo, so `version_before` and `version_after` actually differ when an update lands (the previous `hermes --version` fallback returned the CLI's own static version)
- Human-readable changelog — parses Conventional Commits (`feat:`, `fix:`, `perf:`, ...) and groups them under labeled sections (✨ 新功能 / 🐛 Bug 修复 / ⚡ 性能优化 / ...). Noise commits (`chore`, `style`, `test`, merges, typo/format-only) are filtered out.
- Telegram notification (optional) — configured credentials send, unconfigured silently skipped
- Silent exit when no updates available

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. (Optional) Edit `.env` with your Telegram credentials for notifications:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

   If left empty, the script still runs `hermes update` — just without notifications.

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
