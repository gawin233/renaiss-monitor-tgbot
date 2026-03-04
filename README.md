# renaiss-monitor-tgbot
Automated Renaiss marketplace monitor. Real-time profit detection (Price &lt; FMV), user activity tracking, and Telegram bot integration. High-efficiency arbitrage tool with local data persistence.
# Renaiss 市场与用户动态监控 
本工具是一个基于 Playwright 和 Telegram Bot 的自动化监控程序。它能帮你实时发现 Renaiss 市场中的“捡漏”机会（价格低于 FMV），并追踪特定活跃用户的实时动态。

## 🛠 功能特点

- **智能捡漏**：
  - FMV < $100：利润 >= $5 自动推送。
  - FMV >= $100：利润 >= $10 自动推送。
- **动态追踪**：监控指定用户主页的 `Activity` 选项卡，第一时间获取其上架、成交动作。
- **防骚扰机制**：本地 JSON 数据库存储已推送记录，确保同一条机会不会重复轰炸。
- **多用户支持**：可同时向多个与机器人开启对话的用户推送信息。

## ⚙️ 快速开始

### 1. 环境准备
确保你的电脑安装了 Python 3.8+。
```bash
pip install playwright python-telegram-bot
playwright install chromium
```

### 2. 配置 Telegram Token
安全建议： 不要直接在脚本里改代码。请设置系统环境变量：
```
Mac/Linux: export TG_TOKEN="你的机器人TOKEN"
Windows: set TG_TOKEN=你的机器人TOKEN
或者，你可以在 renaiss.py 的第 12 行填入 Token。
```
### 3.  运行
```
python renaiss.py
```

📝 常用命令
```
/start - 激活机器人并查看功能。
/monitor [用户链接] - 添加一个要追踪的 Renaiss 用户地址。
/list - 查看当前正在监控的目标。
```

📄 存储文件说明
```
renaiss_users_data.json: 存储订阅了推送的 TG 用户 ID。
renaiss_v12_deals.json: 捡漏推送历史，防止重复。
renaiss_user_activity.json: 用户动态的最后状态缓存。
```

免责声明：本脚本仅用于个人学习和自动化实验，请遵守 Renaiss 平台的使用协议。

Renaiss Monitor TG-Bot (v36.7)
Renaiss marketplace monitor. Real-time arbitrage detection (Price < FMV), user activity tracking, and Telegram bot integration. High-efficiency tool with local data persistence.

🛠 Features
Smart Arbitrage Detection:
If FMV < $100: Alert when profit >= $5.
If FMV >= $100: Alert when profit >= $10.

Activity Tracking: Monitor the Activity tab of specific users to capture listings and sales in real-time.
Anti-Spam Mechanism: Local JSON database stores sent alerts to prevent duplicate notifications.
Multi-User Support: Simultaneously push information to multiple Telegram users.

⚙️ Quick Start
### 1.Environment Setup
Ensure you have Python 3.8+ installed.
```Bash
pip install playwright python-telegram-bot
playwright install chromium
```
### 2. Configure Telegram Token
```
Security Note: It is highly recommended to use environment variables instead of hardcoding your token in the script.
Mac/Linux: export TG_TOKEN="YOUR_BOT_TOKEN"
Windows: set TG_TOKEN=YOUR_BOT_TOKEN
Alternatively, you can manually fill in the token on line 12 of renaiss.py.
```
### 3. Run the Script
```Bash
python renaiss.py
```
📝 Commands
```
/start - Activate the bot and view available functions.
/monitor [URL] - Add a specific Renaiss user profile to your tracking list.
/list - View all currently tracked targets.
```

📄 Storage Files
```
renaiss_users_data.json: Stores Telegram User IDs subscribed to alerts.
renaiss_v12_deals.json: History of pushed deals to prevent duplicates.
renaiss_user_activity.json: Cache for user activity status to detect new events.
```
⚠️ Disclaimer
This script is for educational and experimental purposes only. Users are responsible for complying with the Renaiss platform's Terms of Service. The author assumes no responsibility for any account-related risks or financial losses.
