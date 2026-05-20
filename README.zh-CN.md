[English](README.md) | [中文](README.zh-CN.md)

# hermes-daily-update

Hermes Agent 每日自动更新脚本，通过 Telegram 通知更新结果。

## 功能

- `hermes update` 更新 Hermes Agent（代码 + 依赖 + 重启 gateway）
- 检测版本变化
- 显示新版本号
- 显示更新内容（过滤后的 commit 信息，跳过 merge/typo/chore）
- 发送 Telegram 通知（包含版本号、更新内容）
- 自动重启 gateway
- 无更新时静默退出
- **健壮的版本检测**：依次尝试 `hermes --version`、完整路径、package.json、git tags

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
  ... 还有 137 项

正在重启 gateway...
```

## 配置

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 填入你的 Telegram 凭证：
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
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

## 为什么用 Linux Crontab？

Hermes cron 调度器在 gateway 重启时可能错过触发窗口。Linux crontab 独立于 gateway 运行，对时间敏感的每日更新更可靠。

## 为什么 `.env` 放在项目目录？

在 cron 环境中，`HOME` 变量可能被覆盖（例如设为 `~/.hermes` 而非 `~`），导致 `os.path.expanduser("~/.hermes/.env")` 解析为错误路径（如 `~/.hermes/.hermes/.env`）。为避免此问题，脚本使用绝对路径从项目目录读取 `.env` 凭证，更可靠且凭证按项目隔离。

## License

MIT
