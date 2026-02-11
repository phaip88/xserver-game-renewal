# XServer Game Server 自动续期

[![GitHub Actions](https://github.com/phaip88/xserver-game-renewal/actions/workflows/xserver-game-renewal.yml/badge.svg)](https://github.com/phaip88/xserver-game-renewal/actions)

XServer Game Server (ゲーム用マルチサーバー) 自动续期脚本 - 基于 Playwright 框架

---

## 🎯 功能特性

- ✅ 完全自动化续期流程
- ✅ 智能判断续期时机（剩余 < 23 小时）
- ✅ 自动处理 Cloudflare Turnstile 验证
- ✅ Telegram/邮件通知
- ✅ GitHub Actions 定时运行（每 6 小时）
- ✅ 详细日志和截图记录

---

## 🚀 快速开始

### 1. 配置 GitHub Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加：

| Secret 名称 | 说明 |
|------------|------|
| `XSERVER_EMAIL` | XServer 账号邮箱（必填） |
| `XSERVER_PASSWORD` | XServer 账号密码（必填） |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（可选） |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（可选） |

### 2. 启用 Actions

进入 **Actions** 标签页，启用工作流。

### 3. 手动运行测试

点击 **Run workflow** 手动触发一次，验证配置正确。

---

## 📊 运行状态

工作流每 6 小时自动运行一次：
- **UTC 时间**: 00:00, 06:00, 12:00, 18:00
- **北京时间**: 08:00, 14:00, 20:00, 02:00

查看运行状态：[Actions](https://github.com/phaip88/xserver-game-renewal/actions)

---

## 📝 文档

- [完整使用指南](GAME_SERVER_GUIDE.md) - 详细的安装、配置、部署说明
- [GitHub Actions 配置](GITHUB_ACTIONS_SETUP.md) - Actions 详细配置指南
- [快速启动](QUICK_START.md) - 3 分钟快速部署
- [流程对比分析](FLOW_COMPARISON_ANALYSIS.md) - Game Server vs VPS 版本对比
- [项目分析](XSERVER_PROJECT_ANALYSIS.md) - 技术架构分析

---

## 🔧 本地运行

### 安装依赖

```bash
pip install -r game_requirements.txt
playwright install chromium
```

### 配置环境变量

```bash
export XSERVER_EMAIL="your_email@example.com"
export XSERVER_PASSWORD="your_password"
```

### 运行脚本

```bash
python3 xserver_game_renewal.py
```

---

## 📦 项目结构

```
.
├── xserver_game_renewal.py          # 主脚本
├── game_requirements.txt            # Python 依赖
├── .github/workflows/
│   └── xserver-game-renewal.yml    # GitHub Actions 工作流
├── GAME_SERVER_GUIDE.md            # 完整使用指南
├── GITHUB_ACTIONS_SETUP.md         # Actions 配置指南
├── QUICK_START.md                  # 快速启动指南
└── .env.example                    # 环境变量模板
```

---

## ⚠️ 注意事项

1. **首次运行建议本地测试**，确认流程正常
2. **GitHub Actions 必须使用 headless 模式**
3. **Turnstile 验证成功率约 85%**
4. **续期触发阈值默认 23 小时**，可通过环境变量 `TRIGGER_HOUR` 调整

---

## 🆚 与 VPS 版本对比

| 特性 | Game Server 版本 | VPS 版本 |
|------|-----------------|----------|
| 产品 | ゲーム用マルチサーバー | 無料VPS |
| 登录 URL | `/xapanel/login/xserver/` | `/xapanel/login/xvps/` |
| 导航复杂度 | 高（6步） | 低（1-2步） |
| 续期流程 | 三步确认 | 验证码提交 |
| 自动化程度 | 100% | 100% |

---

## 📄 许可证

MIT License

---

## 🙏 致谢

本项目基于 [Xserver-VPS-Renew](https://github.com/akimify/Xserver-VPS-Renew) 改造，感谢原作者的贡献。

---

**最后更新**: 2024-02-11
