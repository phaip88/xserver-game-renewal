# XServer Game Panel 自动续期

自动登录 XServer Game Panel 并执行服务器续期操作的 Python 脚本。

## 功能特点

- ✅ 自动登录 Game Panel
- ✅ 提取服务器到期时间
- ✅ 智能判断是否需要续期
- ✅ 自动点击续期按钮
- ✅ Telegram 通知
- ✅ GitHub Actions 自动化运行
- ✅ 多种时间格式支持
- ✅ **智能调度**：根据到期时间自动计算下次检查时间
- ✅ **缓存机制**：避免不必要的检查，节省资源

## 快速开始

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
playwright install chromium
```

2. 设置环境变量：
```bash
# Windows PowerShell
$env:GAME_LOGIN_ID = "your_login_id"
$env:GAME_PASSWORD = "your_game_panel_password"
$env:DOMAIN_OR_IP = "your_domain_or_ip"
$env:TELEGRAM_BOT_TOKEN = "your_bot_token"
$env:TELEGRAM_CHAT_ID = "your_chat_id"
$env:USE_HEADLESS = "false"  # 本地测试时设为 false 可以看到浏览器
```

3. 运行脚本：
```bash
python xserver_game_panel_renewal.py
```

### GitHub Actions 自动化

1. Fork 本仓库

2. 在仓库设置中添加以下 Secrets：
   - `GAME_LOGIN_ID`: ログインID
   - `GAME_PASSWORD`: ゲームパネルパスワード
   - `DOMAIN_OR_IP`: ご利用中のドメイン または IPアドレス
   - `TELEGRAM_BOT_TOKEN`: Telegram Bot Token（可选）
   - `TELEGRAM_CHAT_ID`: Telegram Chat ID（可选）

3. 启用 GitHub Actions

4. 工作流会自动每天执行一次（北京时间 08:00），但脚本内部会智能判断：
   - 首次运行：执行完整检查，获取到期时间，保存到 `NEXT_RUN.md`
   - 后续运行：读取 `NEXT_RUN.md` 判断是否到达检查时间
   - 未到检查时间：直接跳过，不消耗资源
   - 已到检查时间：执行完整检查流程
   - 可以在 GitHub 上直接查看 `NEXT_RUN.md` 了解下次执行时间

## 智能调度机制

### 工作原理

1. **首次运行**：
   - 登录并获取服务器到期时间
   - 计算"下次检查时间" = 到期时间 - 24小时
   - 保存到 `NEXT_RUN.md` 文件（可在 GitHub 上直接查看）

2. **后续运行**：
   - 读取 `NEXT_RUN.md` 中的"下次检查时间"
   - 如果当前时间 < 下次检查时间：跳过本次运行
   - 如果当前时间 >= 下次检查时间：执行完整检查

3. **续期后**：
   - 重新获取新的到期时间
   - 重新计算下次检查时间
   - 更新 `NEXT_RUN.md`

### 优势

- ⚡ **节省资源**：大部分时间只需读取文件，不启动浏览器
- 🎯 **精准调度**：在需要的时候才执行检查
- 💰 **降低成本**：减少 GitHub Actions 使用时间
- 🔄 **自动适应**：根据实际到期时间动态调整
- 👀 **可视化**：可以在 GitHub 上直接查看 `NEXT_RUN.md` 了解下次执行时间

### 示例

假设服务器到期时间是 `2026-02-14 23:59`：

1. **2026-02-11 08:00** - 首次运行
   - 获取到期时间：2026-02-14 23:59
   - 计算下次检查：2026-02-13 23:59（到期前24小时）
   - 保存到 `NEXT_RUN.md`

2. **2026-02-12 08:00** - 每天运行
   - 读取 `NEXT_RUN.md`：下次检查时间是 2026-02-13 23:59
   - 当前时间 < 下次检查时间
   - ⏸️ 跳过本次运行（仅耗时 1-2 秒）

3. **2026-02-14 08:00** - 到达检查时间
   - 读取 `NEXT_RUN.md`：下次检查时间是 2026-02-13 23:59
   - 当前时间 >= 下次检查时间
   - ✅ 执行完整检查流程
   - 剩余时间 < 23 小时，执行续期
   - 更新 `NEXT_RUN.md`

## 配置说明

### 环境变量

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| `GAME_LOGIN_ID` | ログインID | ✅ | - |
| `GAME_PASSWORD` | ゲームパネルパスワード | ✅ | - |
| `DOMAIN_OR_IP` | ドメイン または IPアドレス | ✅ | - |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | ❌ | - |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | ❌ | - |
| `USE_HEADLESS` | 无头模式 | ❌ | `true` |
| `TRIGGER_HOUR` | 续期触发阈值（小时） | ❌ | `23` |

### 续期触发逻辑

- 脚本会提取服务器到期时间
- 计算剩余时间（小时）
- 如果剩余时间 < `TRIGGER_HOUR`，则执行续期
- 默认阈值为 23 小时

## 支持的时间格式

脚本支持以下时间格式：

1. `2024年02月15日 23:59まで` - 日本日期格式
2. `(2026-02-14まで)` - ISO 日期格式
3. `あと 2日 5時間` - 相对时间（天+小时）
4. `残り64時間23分` - 剩余时间（小时+分钟）

## Telegram 通知

### 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新 Bot
3. 获取 Bot Token

### 获取 Chat ID

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息获取你的 Chat ID

### 通知内容

- ✅ 续期成功通知
- ℹ️ 尚未到期通知
- ❌ 执行失败通知

## 工作流程

1. 启动浏览器（Chromium）
2. 访问登录页面
3. 填写登录信息（3个字段）
4. 提交登录表单
5. 验证登录成功
6. 提取到期时间
7. 判断是否需要续期
8. 如需续期，点击"アップグレード・期限延長"按钮
9. 发送 Telegram 通知
10. 生成状态报告

## 故障排除

### 登录失败

- 检查环境变量是否正确设置
- 确认账号密码正确
- 查看截图文件 `01_login_page.png` 和 `02_before_login.png`

### 无法提取到期时间

- 检查是否登录成功
- 查看日志中的 `📋 页面上的 span 元素` 输出
- 查看截图文件 `04_no_ttl_text.png`

### 无法找到续期按钮

- 检查日志中的 `📋 页面上的链接和按钮` 输出
- 确认页面上是否有"アップグレード・期限延長"按钮
- 查看截图文件 `error_no_extend_button.png`

## 日志文件

- `game_panel_renewal.log` - 详细运行日志
- `*.png` - 各步骤截图
- `game_panel_cache.json` - 缓存文件

## 许可证

MIT License

## 免责声明

本脚本仅供学习和个人使用。使用本脚本所产生的任何后果由使用者自行承担。

---

*最后更新: 2026-02-11*
