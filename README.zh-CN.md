[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent 每日自动更新脚本，可选 Telegram 通知。

## 功能

- **始终执行 `hermes update`** — 确保代码、依赖和 gateway 保持最新
- 检测版本变化，显示更新日志
- Telegram 通知（可选）— 配置了凭证就发送，未配置则静默跳过
- 无更新时静默退出

## 配置

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. （可选）编辑 `.env` 填入 Telegram 凭证以接收通知：
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

   留空也可以，脚本仍会正常执行 `hermes update`，只是不发通知。

## 使用

```bash
python3 hermes_daily_update.py
```

### Linux Crontab（推荐）

```bash
# 北京时间 01:05（UTC 17:05）
5 17 * * * /usr/bin/python3 /path/to/hermes_daily_update.py >> /path/to/logs/daily_update.log 2>&1
```

## 为什么用 Linux Crontab？

Hermes cron 调度器在 gateway 重启时可能错过触发窗口。Linux crontab 独立于 gateway 运行，对时间敏感的每日更新更可靠。

## 为什么 `.env` 放在项目目录？

在 cron 环境中，`HOME` 变量可能被覆盖（例如设为 `~/.hermes` 而非 `~`），导致 `os.path.expanduser("~/.hermes/.env")` 解析为错误路径（如 `~/.hermes/.hermes/.env`）。为避免此问题，脚本使用绝对路径从项目目录读取 `.env` 凭证，更可靠且凭证按项目隔离。

## License

MIT
