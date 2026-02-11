# GitHub Actions 自动续期配置指南

## 📋 概述

已创建 GitHub Actions 工作流 `.github/workflows/xserver-game-renewal.yml`，实现 XServer Game Server 的自动续期。

---

## ⚙️ 配置步骤

### 步骤 1：配置 GitHub Secrets

进入你的 GitHub 仓库，依次点击：
```
Settings → Secrets and variables → Actions → New repository secret
```

#### 必填 Secrets

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `XSERVER_EMAIL` | XServer 账号邮箱 | `your_email@example.com` |
| `XSERVER_PASSWORD` | XServer 账号密码 | `your_password` |

#### 可选 Secrets（通知功能）

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 通过 @BotFather 创建 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 通过 @userinfobot 获取 |
| `SENDER_EMAIL` | 发件邮箱（QQ邮箱） | 你的 QQ 邮箱 |
| `SENDER_PASSWORD` | 邮箱授权码 | QQ邮箱设置中获取 |
| `RECEIVER_EMAIL` | 收件邮箱 | 接收通知的邮箱 |

### 步骤 2：推送代码到 GitHub

```bash
# 添加所有文件
git add .

# 提交
git commit -m "添加 XServer Game Server 自动续期脚本"

# 推送到 GitHub
git push origin main
```

### 步骤 3：启用 GitHub Actions

1. 进入仓库的 **Actions** 标签页
2. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**
3. 找到 **"🎮 XServer Game Server 自动续期"** 工作流

---

## 🕐 运行时间

### 自动运行

工作流会在以下时间自动运行（UTC 时间）：
- 每天 00:00, 06:00, 12:00, 18:00

对应北京时间（UTC+8）：
- 每天 08:00, 14:00, 20:00, 02:00

### 手动运行

1. 进入 **Actions** 标签页
2. 选择 **"🎮 XServer Game Server 自动续期"**
3. 点击右侧 **"Run workflow"** 按钮
4. 选择分支（通常是 `main`）
5. 点击 **"Run workflow"** 确认

---

## 📊 查看运行结果

### 方法 1：查看 Actions 日志

1. 进入 **Actions** 标签页
2. 点击最新的工作流运行记录
3. 查看各步骤的详细日志

### 方法 2：下载日志和截图

1. 在工作流运行详情页面
2. 滚动到底部 **Artifacts** 区域
3. 下载 `renewal-logs-xxx.zip`
4. 解压查看：
   - `game_renewal.log` - 详细日志
   - `*.png` - 各步骤截图
   - `README.md` - 状态报告
   - `game_cache.json` - 缓存数据

### 方法 3：查看仓库 README.md

工作流会自动更新仓库根目录的 `README.md`，显示最新的续期状态。

---

## 🔧 工作流配置说明

### 定时任务配置

```yaml
schedule:
  - cron: '0 */6 * * *'  # 每6小时运行一次
```

如果想修改运行频率，可以调整 cron 表达式：

| 频率 | Cron 表达式 | 说明 |
|------|------------|------|
| 每 3 小时 | `0 */3 * * *` | 更频繁检查 |
| 每 12 小时 | `0 */12 * * *` | 减少运行次数 |
| 每天 1 次 | `0 0 * * *` | 每天 UTC 00:00 |
| 每天 2 次 | `0 0,12 * * *` | 每天 UTC 00:00 和 12:00 |

### 环境变量配置

```yaml
env:
  USE_HEADLESS: 'true'      # 无头模式（必须为 true）
  TRIGGER_HOUR: '23'        # 续期触发阈值（小时）
```

可调整参数：
- `TRIGGER_HOUR`: 剩余时间小于此值时才续期（默认 23 小时）
- `USE_HEADLESS`: GitHub Actions 必须使用无头模式

---

## 🎯 工作流程

```
1. 📥 检出代码
   ↓
2. 🐍 设置 Python 3.11 环境
   ↓
3. 📦 安装 Python 依赖 (playwright, aiohttp)
   ↓
4. 🌐 安装 Chromium 浏览器
   ↓
5. 🚀 运行续期脚本
   ├─ 登录 XServer
   ├─ 导航到续期页面（6步）
   ├─ 提取到期时间
   ├─ 判断是否需要续期
   └─ 执行续期操作（3步确认）
   ↓
6. 📊 上传日志和截图（保留 30 天）
   ↓
7. 📝 提交状态报告到仓库
```

---

## 🔍 故障排查

### 问题 1：工作流运行失败

**检查步骤**：
1. 查看 Actions 日志，找到失败的步骤
2. 检查 Secrets 是否配置正确
3. 下载 Artifacts 查看详细日志和截图

### 问题 2：Secrets 未生效

**解决方案**：
1. 确认 Secret 名称完全匹配（区分大小写）
2. 重新保存 Secret
3. 手动触发工作流测试

### 问题 3：Headless 模式问题

**说明**：
- GitHub Actions 必须使用 headless 模式
- 如果 Turnstile 验证失败，脚本会尝试多种方法
- 预期成功率约 85%

### 问题 4：时区问题

**说明**：
- GitHub Actions 使用 UTC 时区
- 脚本内部使用 JST (UTC+9) 处理 XServer 时间
- 通知时间会转换为 UTC+8 (北京时间)

---

## 📈 监控建议

### 1. 启用通知

配置 Telegram 或邮件通知，及时了解续期状态：
- ✅ 续期成功
- ℹ️ 尚未到期
- ❌ 续期失败

### 2. 定期检查

建议每周检查一次：
1. Actions 运行记录
2. 仓库 README.md 状态
3. 下载最新的日志和截图

### 3. 设置提醒

在 GitHub 仓库设置中：
```
Settings → Notifications → Actions
```
勾选 **"Send notifications for failed workflows only"**

---

## 🔒 安全建议

1. **不要在代码中硬编码密码**
   - 始终使用 GitHub Secrets

2. **定期更新密码**
   - 更新后记得同步更新 Secrets

3. **限制仓库访问权限**
   - 如果是私有仓库，控制协作者权限

4. **定期检查 Actions 日志**
   - 确保没有敏感信息泄露

---

## 📚 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Cron 表达式生成器](https://crontab.guru/)
- [Playwright 文档](https://playwright.dev/python/)

---

## ✅ 配置检查清单

- [ ] 已配置 `XSERVER_EMAIL` Secret
- [ ] 已配置 `XSERVER_PASSWORD` Secret
- [ ] 已配置通知 Secrets（可选）
- [ ] 已推送代码到 GitHub
- [ ] 已启用 GitHub Actions
- [ ] 已手动运行一次测试
- [ ] 已检查运行日志
- [ ] 已下载并查看 Artifacts

---

**配置完成后，脚本将自动每 6 小时检查一次，并在需要时自动续期！** 🎉
