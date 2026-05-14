# hermes-daily-update

Hermes Agent 每日自动更新脚本，通过 Telegram 通知更新结果。

## 功能

- `git pull` 更新 Hermes Agent 代码
- 检测版本变化
- 发送 Telegram 通知（成功/失败）
- 自动重启 gateway

## 配置

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 填入你的 Telegram 配置：
   ```
   TELEGRAM_BOT_TOKEN=你的Bot Token
   TELEGRAM_CHAT_ID=你的Chat ID
   ```

## 使用

```bash
python3 hermes_daily_update.py
```

建议配合 crontab 每日自动运行：
```bash
0 7 * * * /usr/bin/python3 /path/to/hermes_daily_update.py
```
