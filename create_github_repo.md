# 创建 GitHub 仓库并推送代码

## 方式 1：使用脚本（推荐）

### 步骤 1：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `xserver-game-renewal`
   - **Description**: `XServer Game Server 自动续期脚本 - Playwright 版本`
   - **Visibility**: Private（推荐）或 Public
   - **不要勾选** "Add a README file"
   - **不要勾选** "Add .gitignore"
   - **不要勾选** "Choose a license"
3. 点击 **"Create repository"**

### 步骤 2：运行推送脚本

双击运行 `push_to_github.bat`，按提示操作：
1. 脚本会自动初始化 Git、添加文件、提交
2. 当提示输入 Token 时，粘贴你的新 Token（不是刚才那个！）
3. 等待推送完成

---

## 方式 2：手动命令

### 步骤 1：创建仓库（同上）

### 步骤 2：执行命令

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 配置用户信息
git config user.name "phaip88"
git config user.email "phaip88@users.noreply.github.com"

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "🎮 添加 XServer Game Server 自动续期功能"

# 5. 添加远程仓库
git remote add origin https://github.com/phaip88/xserver-game-renewal.git

# 6. 推送（会提示输入用户名和 Token）
git push -u origin main
```

**推送时的认证**：
- Username: `phaip88`
- Password: 粘贴你的新 Token（不是密码！）

---

## 方式 3：使用 GitHub Desktop（最简单）

### 步骤 1：安装 GitHub Desktop

下载：https://desktop.github.com/

### 步骤 2：登录账号

打开 GitHub Desktop，登录你的 GitHub 账号

### 步骤 3：发布仓库

1. File → Add Local Repository → 选择当前目录
2. 点击 "Publish repository"
3. 填写仓库名：`xserver-game-renewal`
4. 选择 Private 或 Public
5. 点击 "Publish repository"

---

## ⚠️ 重要提示

### 1. Token 安全

- ❌ 不要在聊天、代码、文档中暴露 Token
- ✅ Token 只在推送时输入一次
- ✅ 推送后 Git 会记住凭据（Windows Credential Manager）

### 2. 仓库名称

如果你想用其他名称，修改以下位置：
- `push_to_github.bat` 中的 `origin` URL
- 或手动命令中的 URL

### 3. 分支名称

- 默认使用 `main` 分支
- 如果你的默认分支是 `master`，将命令中的 `main` 改为 `master`

---

## 推送后的操作

### 1. 配置 GitHub Secrets

```
仓库页面 → Settings → Secrets and variables → Actions → New repository secret
```

添加：
- `XSERVER_EMAIL` = 你的 XServer 邮箱
- `XSERVER_PASSWORD` = 你的 XServer 密码

### 2. 启用 Actions

```
仓库页面 → Actions → 启用工作流
```

### 3. 手动运行测试

```
Actions → 🎮 XServer Game Server 自动续期 → Run workflow
```

---

## 🆘 遇到问题？

### 问题 1：推送被拒绝

```
error: failed to push some refs
```

**解决**：
```bash
git pull origin main --rebase
git push -u origin main
```

### 问题 2：仓库已存在

**解决**：
1. 删除远程仓库重新创建
2. 或使用 force push（谨慎）：
```bash
git push -u origin main --force
```

### 问题 3：认证失败

**解决**：
1. 确认 Token 有 `repo` 权限
2. 确认 Token 没有过期
3. 重新生成 Token

---

## ✅ 成功标志

推送成功后，你应该能在 GitHub 看到：
- ✅ 所有代码文件
- ✅ `.github/workflows/` 目录
- ✅ Actions 标签页有工作流
- ✅ README.md 显示正常

---

**选择一种方式开始吧！推荐使用脚本方式（最简单）。** 🚀
