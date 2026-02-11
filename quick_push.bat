@echo off
chcp 65001 >nul

REM ========================================
REM 快速推送脚本 - 直接设置 Token 并推送
REM ========================================

REM 设置你的 GitHub Token (替换下面的 YOUR_TOKEN_HERE)
set GITHUB_TOKEN=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

REM 设置 GitHub 用户名
set GITHUB_USER=phaip88

REM 设置仓库名
set REPO_NAME=xserver-game-renewal

REM ========================================
REM 开始推送
REM ========================================

echo ========================================
echo GitHub 快速推送
echo ========================================
echo.

REM 检查 Token 是否设置
if "%GITHUB_TOKEN%"=="YOUR_TOKEN_HERE" (
    echo ❌ 错误: 请先编辑此脚本，设置你的 GITHUB_TOKEN
    echo.
    echo 步骤:
    echo 1. 右键编辑 quick_push.bat
    echo 2. 将第 9 行的 YOUR_TOKEN_HERE 替换为你的真实 Token
    echo 3. 保存后重新运行
    echo.
    pause
    exit /b 1
)

echo [1/6] 初始化 Git 仓库...
if not exist .git (
    git init
) else (
    echo Git 仓库已存在
)
echo.

echo [2/6] 配置 Git 用户信息...
git config user.name "%GITHUB_USER%"
git config user.email "%GITHUB_USER%@users.noreply.github.com"
echo.

echo [3/6] 添加文件到暂存区...
git add .
echo.

echo [4/6] 提交更改...
git commit -m "🎮 添加 XServer Game Server 自动续期功能

- 添加 Playwright 自动续期脚本
- 配置 GitHub Actions 工作流
- 添加完整文档和配置指南
- 支持 Telegram/邮件通知
- 智能续期判断（剩余 < 23 小时）"
echo.

echo [5/6] 设置远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo.

echo [6/6] 推送到 GitHub...
git push https://%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%REPO_NAME%.git main --force
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo ✅ 推送成功！
    echo ========================================
    echo.
    echo 仓库地址: https://github.com/%GITHUB_USER%/%REPO_NAME%
    echo.
    echo 下一步：
    echo 1. 访问仓库 Settings → Secrets and variables → Actions
    echo 2. 添加 XSERVER_EMAIL 和 XSERVER_PASSWORD
    echo 3. 进入 Actions 标签页启用工作流
    echo 4. 手动运行一次测试
    echo.
) else (
    echo ========================================
    echo ❌ 推送失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 仓库不存在 - 请先在 GitHub 创建仓库
    echo 2. Token 权限不足 - 确保 token 有 repo 权限
    echo 3. Token 已过期 - 重新生成 token
    echo 4. 网络问题 - 检查网络连接
    echo.
)

pause
