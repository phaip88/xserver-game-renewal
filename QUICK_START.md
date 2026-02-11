# 🚀 XServer Game Server 自动续期 - 快速启动

## 📦 文件清单

```
xserver_game_renewal.py          # 主脚本
game_requirements.txt            # Python 依赖
GAME_SERVER_GUIDE.md            # 详细使用指南
GITHUB_ACTIONS_SETUP.md         # GitHub Actions 配置指南
.github/workflows/xserver-game-renewal.yml  # 工作流文件
```

---

## ⚡ 3 分钟快速部署

### 方式 1：GitHub Actions（推荐）

```bash
# 1. 推送代码到 GitHub
git add .
git commit -m "添加 XServer Game Server 自动续期"
git push origin main

# 2. 配置 GitHub Secrets
# 进入仓库 Settings → Secrets and variables → Actions
# 添加以下 Secrets：
#   - XSERVER_EMAIL (必填)
#   - XSERVER_PASSWORD (必填)
#   - TELEGRAM_BOT_TOKEN (可选)
#   - TELEGRAM_CHAT_ID (可选)

# 3. 启用 Actions
# 进入仓库 Actions 标签页，启用工作流

# 4. 手动运行测试
# Actions → 选择工作流 → Run workflow
```

**详细步骤**: 查看 `GITHUB_ACTIONS_SETUP.md`

---

### 方式 2：本地测试

```bash
# 1. 安装依赖
pip install -r game_requirements.txt
playwright install chromium

# 2. 配置环境变量 (Windows)
set XSERVER_EMAIL=your_email@example.com
set XSERVER_PASSWORD=your_password

# 或配置环境变量 (Linux/Mac)
export XSERVER_EMAIL="your_email@example.com"
export XSERVER_PASSWORD="your_password"

# 3. 运行脚本
python xserver_game_renewal.py

# 4. 查看结果
# - game_renewal.log (日志)
# - *.png (截图)
# - README.md (状态报告)
```

---

### 方式 3：青龙面板

```bash
# 1. 进入青龙容器
docker exec -it qinglong bash

# 2. 安装依赖
pip3 install playwright aiohttp
playwright install chromium
playwright install-deps chromium

# 3. 上传脚本到 /ql/scripts/xserver_game_renewal.py

# 4. 配置环境变量 (青龙面板 → 环境变量)
XSERVER_EMAIL=your_email@example.com
XSERVER_PASSWORD=your_password

# 5. 添加定时任务 (青龙面板 → 定时任务)
# 名称：XServer Game Server 自动续期
# 命令：python3 /ql/scripts/xserver_game_renewal.py
# 定时：0 */6 * * *
```

---

## 🎯 运行逻辑

```
脚本每次运行时：

1. 登录 XServer
2. 导航到续期页面（6步）
3. 提取到期时间
4. 计算剩余时间

如果剩余时间 < 23 小时：
  → 执行续期操作（3步确认）
  → 发送成功通知

如果剩余时间 >= 23 小时：
  → 跳过续期
  → 发送"尚未到期"通知
```

---

## 📊 运行频率建议

| 部署方式 | 推荐频率 | Cron 表达式 |
|---------|---------|------------|
| GitHub Actions | 每 6 小时 | `0 */6 * * *` |
| 青龙面板 | 每 6 小时 | `0 */6 * * *` |
| 本地 Cron | 每 6 小时 | `0 */6 * * *` |

**说明**：
- 续期触发阈值默认为 23 小时
- 每 6 小时检查一次，确保不会错过续期窗口
- 脚本会自动判断是否需要续期，不会重复续期

---

## 🔔 通知配置（可选）

### Telegram 通知

1. 创建 Bot：
   - 在 Telegram 搜索 `@BotFather`
   - 发送 `/newbot` 创建新 Bot
   - 获取 `Bot Token`

2. 获取 Chat ID：
   - 在 Telegram 搜索 `@userinfobot`
   - 发送任意消息获取你的 `Chat ID`

3. 配置环境变量：
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### 邮件通知（QQ 邮箱）

1. 获取授权码：
   - 登录 QQ 邮箱
   - 设置 → 账户 → POP3/IMAP/SMTP
   - 开启服务并生成授权码

2. 配置环境变量：
   ```bash
   SENDER_EMAIL=your_qq@qq.com
   SENDER_PASSWORD=your_auth_code
   RECEIVER_EMAIL=your_qq@qq.com
   ```

---

## 🔍 查看运行结果

### 本地运行

```bash
# 查看日志
cat game_renewal.log

# 查看状态报告
cat README.md

# 查看截图
ls *.png
```

### GitHub Actions

1. 进入仓库 **Actions** 标签页
2. 点击最新的工作流运行
3. 查看日志或下载 Artifacts

### 青龙面板

1. 进入 **日志管理**
2. 找到对应的任务日志
3. 查看运行详情

---

## ⚠️ 重要提示

1. **首次运行建议本地测试**
   - 确认账号密码正确
   - 验证导航流程正常
   - 检查截图和日志

2. **GitHub Actions 限制**
   - 必须使用 headless 模式
   - Turnstile 验证成功率约 85%
   - 失败时会自动重试

3. **安全建议**
   - 不要在代码中硬编码密码
   - 使用环境变量或 Secrets
   - 定期更新密码

4. **时区说明**
   - XServer 使用 JST (UTC+9)
   - 脚本自动处理时区转换
   - 通知时间为北京时间 (UTC+8)

---

## 📚 详细文档

- **完整使用指南**: `GAME_SERVER_GUIDE.md`
- **GitHub Actions 配置**: `GITHUB_ACTIONS_SETUP.md`
- **流程对比分析**: `FLOW_COMPARISON_ANALYSIS.md`
- **项目分析**: `XSERVER_PROJECT_ANALYSIS.md`

---

## 🆘 遇到问题？

1. 查看 `GAME_SERVER_GUIDE.md` 的故障排查章节
2. 检查日志文件 `game_renewal.log`
3. 查看截图文件了解失败位置
4. 确认账号密码和网络连接

---

**开始使用吧！选择一种部署方式，3 分钟即可完成配置。** 🎉
