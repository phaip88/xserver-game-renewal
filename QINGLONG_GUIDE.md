# XServer 自动续期脚本 - 青龙面板部署指南

## 📋 分析结论

### ❌ 原脚本不适合青龙面板的原因：

1. **Crontab 冲突** - 脚本会直接操作系统 crontab，与青龙面板的任务调度冲突
2. **交互式输入** - 使用 `getpass.getpass()` 需要手动输入验证码，无法自动化
3. **资源消耗大** - Selenium + Chrome 需要大量内存（200-500MB）
4. **路径硬编码** - 所有路径都是硬编码，不适配青龙环境

### ✅ 改造方案

我已经创建了 `xserver_qinglong_adapted.py`（青龙适配版），主要改动：

#### 1. 移除 Crontab 操作
```python
# 原版：脚本自己管理 crontab
delete_default_crontab()
add_once_crontab(delay_hours)

# 青龙版：由青龙面板管理定时任务
# 在青龙面板设置：0 9 * * * （每天9点执行）
```

#### 2. 移除交互式验证码
```python
# 原版：需要手动输入
verify_code = getpass.getpass(prompt="输入验证码：")

# 青龙版：需要提前配置或跳过验证
# 建议：首次在本地运行，保存 Cookie 后上传到青龙
```

#### 3. 使用环境变量配置
```python
# 原版：硬编码
USER_EMAIL = "Xserver账号"
CHROMEDRIVER_PATH = "/root/.cache/selenium/..."

# 青龙版：环境变量
USER_EMAIL = os.getenv("XSERVER_EMAIL")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
```

#### 4. 集成青龙通知
```python
# 支持青龙面板内置通知 + 邮件备用
send_notification("续期成功", "详细信息...")
```

## 🚀 青龙面板部署步骤

### 步骤 1：安装依赖

在青龙面板容器中执行：

```bash
# 进入青龙容器
docker exec -it qinglong bash

# 安装 Python 依赖
pip3 install selenium pytz

# 安装 Chrome 和 ChromeDriver
apt-get update
apt-get install -y chromium chromium-driver

# 或者使用 Alpine 版本
apk add chromium chromium-chromedriver
```

### 步骤 2：配置环境变量

在青龙面板 `配置文件` → `config.sh` 中添加：

```bash
# XServer 账号配置
export XSERVER_EMAIL="your_email@example.com"
export XSERVER_PASSWORD="your_password"

# ChromeDriver 路径
export CHROMEDRIVER_PATH="/usr/bin/chromedriver"

# 邮件通知配置（可选）
export SMTP_SERVER="smtp.qq.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your_qq@qq.com"
export SENDER_PASSWORD="your_smtp_auth_code"
export RECEIVER_EMAIL="your_qq@qq.com"

# 续期触发阈值（小时）
export TRIGGER_HOUR="23"
```

### 步骤 3：上传脚本

1. 将 `xserver_qinglong_adapted.py` 上传到青龙面板
2. 路径：`/ql/scripts/xserver_qinglong_adapted.py`

### 步骤 4：添加定时任务

在青龙面板 `定时任务` 中添加：

```
名称：XServer自动续期
命令：python3 /ql/scripts/xserver_qinglong_adapted.py
定时规则：0 9 * * *
```

## ⚠️ 重要注意事项

### 1. 验证码问题

**问题**：XServer 登录可能需要邮箱验证码

**解决方案**：
- **方案A**：首次在本地运行，保存 Cookie 后上传
- **方案B**：使用 XServer API（如果有）
- **方案C**：配置白名单 IP（联系 XServer 客服）

### 2. 内存占用

Selenium + Chrome 会占用较多内存：
- 最小配置：1GB RAM
- 推荐配置：2GB+ RAM

如果青龙面板内存不足，建议：
- 使用轻量级方案（见下方）
- 或者在独立服务器运行原版脚本

### 3. Cookie 持久化

为了避免频繁登录验证，建议：

```python
# 保存 Cookie
import pickle
pickle.dump(driver.get_cookies(), open("xserver_cookies.pkl", "wb"))

# 加载 Cookie
cookies = pickle.load(open("xserver_cookies.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)
```

## 💡 轻量级替代方案

如果青龙面板资源有限，建议使用 **requests + BeautifulSoup** 替代 Selenium：

### 优点：
- ✅ 内存占用小（< 50MB）
- ✅ 运行速度快
- ✅ 不需要 Chrome/ChromeDriver

### 缺点：
- ❌ 需要手动处理 JavaScript 渲染
- ❌ 需要分析网络请求
- ❌ 可能需要处理反爬虫

## 📊 对比总结

| 特性 | 原版脚本 | 青龙适配版 | 轻量级方案 |
|------|---------|-----------|-----------|
| Crontab 管理 | ✅ 自动 | ❌ 手动 | ❌ 手动 |
| 验证码处理 | ✅ 交互式 | ❌ 需配置 | ❌ 需配置 |
| 内存占用 | 高（500MB+） | 高（500MB+） | 低（<50MB） |
| 青龙兼容 | ❌ 不兼容 | ✅ 兼容 | ✅ 兼容 |
| 部署难度 | 简单 | 中等 | 困难 |

## 🎯 推荐方案

### 场景 1：有独立服务器
→ 使用**原版脚本**，功能最完整

### 场景 2：青龙面板（内存充足 2GB+）
→ 使用**青龙适配版**，需要配置 Cookie

### 场景 3：青龙面板（内存不足 <1GB）
→ 使用**轻量级方案**（需要重写）

## 📝 总结

原脚本设计用于独立服务器环境，**不建议直接在青龙面板运行**。如果必须使用青龙面板，需要：

1. 移除 crontab 操作逻辑
2. 解决验证码自动化问题
3. 确保足够的内存资源
4. 使用环境变量配置

建议：**在独立服务器运行原版脚本**，或者**重写为轻量级 API 版本**。
