# 直接命令推送到 GitHub

## 方式 1：单行命令（最简单）

### 步骤 1：设置环境变量

在命令行中执行（替换 `YOUR_TOKEN` 为你的真实 Token）：

```cmd
set GITHUB_TOKEN=YOUR_TOKEN
```

### 步骤 2：执行推送命令

复制以下命令，一次性执行：

```cmd
git init && git config user.name "phaip88" && git config user.email "phaip88@users.noreply.github.com" && git add . && git commit -m "🎮 添加 XServer Game Server 自动续期功能" && git remote remove origin 2>nul & git remote add origin https://github.com/phaip88/xserver-game-renewal.git && git push https://%GITHUB_TOKEN%@github.com/phaip88/xserver-game-renewal.git main --force
```

---

## 方式 2：分步命令

### 步骤 1：设置 Token

```cmd
set GITHUB_TOKEN=YOUR_TOKEN
```

### 步骤 2：初始化 Git

```cmd
git init
```

### 步骤 3：配置用户信息

```cmd
git config user.name "phaip88"
git config user.email "phaip88@users.noreply.github.com"
```

### 步骤 4：添加文件

```cmd
git add .
```

### 步骤 5：提交

```cmd
git commit -m "🎮 添加 XServer Game Server 自动续期功能"
```

### 步骤 6：添加远程仓库

```cmd
git remote add origin https://github.com/phaip88/xserver-game-renewal.git
```

### 步骤 7：推送

```cmd
git push https://%GITHUB_TOKEN%@github.com/phaip88/xserver-game-renewal.git main --force
```

---

## 方式 3：使用脚本（推荐）

### 选项 A：quick_push.bat（最简单）

1. 右键编辑 `quick_push.bat`
2. 将第 9 行的 `YOUR_TOKEN_HERE` 替换为你的真实 Token：
   ```bat
   set GITHUB_TOKEN=ghp_你的真实Token
   ```
3. 保存并双击运行

### 选项 B：setup_github_token.bat + push_to_github.bat

1. 双击运行 `setup_github_token.bat`
2. 选择选项 1（临时设置）或 2（永久设置）
3. 粘贴你的 Token
4. 双击运行 `push_to_github.bat`

---

## 方式 4：PowerShell 命令

```powershell
# 设置环境变量
$env:GITHUB_TOKEN = "YOUR_TOKEN"

# 推送
git init
git config user.name "phaip88"
git config user.email "phaip88@users.noreply.github.com"
git add .
git commit -m "🎮 添加 XServer Game Server 自动续期功能"
git remote add origin https://github.com/phaip88/xserver-game-renewal.git
git push "https://$env:GITHUB_TOKEN@github.com/phaip88/xserver-game-renewal.git" main --force
```

---

## ⚠️ 重要提示

### 1. Token 安全

- ❌ 不要将 Token 提交到 Git 仓库
- ❌ 不要在公开场合分享 Token
- ✅ 使用环境变量存储 Token
- ✅ Token 使用完后可以删除

### 2. 仓库必须先创建

在推送前，必须先在 GitHub 创建仓库：
1. 访问 https://github.com/new
2. Repository name: `xserver-game-renewal`
3. Visibility: Private（推荐）
4. 不要勾选任何选项
5. 点击 Create repository

### 3. Token 权限

生成 Token 时，必须勾选：
- ✅ `repo` (完整权限)

### 4. 强制推送

命令中使用了 `--force`，会覆盖远程仓库。如果仓库已有内容，请谨慎使用。

---

## 🔍 验证推送成功

推送成功后，访问：
```
https://github.com/phaip88/xserver-game-renewal
```

应该能看到：
- ✅ 所有代码文件
- ✅ `.github/workflows/` 目录
- ✅ README.md 等文档

---

## 🆘 常见问题

### 问题 1：仓库不存在

```
remote: Repository not found.
```

**解决**：先在 GitHub 创建仓库

### 问题 2：认证失败

```
remote: Invalid username or password.
```

**解决**：
1. 检查 Token 是否正确
2. 检查 Token 权限是否包含 `repo`
3. 重新生成 Token

### 问题 3：推送被拒绝

```
error: failed to push some refs
```

**解决**：使用 `--force` 强制推送（命令中已包含）

---

## ✅ 推荐方式

**最简单**: 使用 `quick_push.bat` 脚本
1. 编辑脚本设置 Token
2. 双击运行
3. 完成！

**最安全**: 使用 `setup_github_token.bat` 设置环境变量
1. 运行设置脚本
2. 选择永久设置
3. 运行推送脚本
4. Token 不会出现在代码中

---

**选择一种方式开始吧！** 🚀
