@echo off
chcp 65001 >nul
echo ========================================
echo GitHub 推送脚本
echo ========================================
echo.

REM 检查是否已初始化 Git
if not exist .git (
    echo [1/6] 初始化 Git 仓库...
    git init
    echo.
) else (
    echo [1/6] Git 仓库已存在
    echo.
)

REM 配置 Git 用户信息
echo [2/6] 配置 Git 用户信息...
git config user.name "phaip88"
git config user.email "phaip88@users.noreply.github.com"
echo.

REM 添加所有文件
echo [3/6] 添加文件到暂存区...
git add .
echo.

REM 提交
echo [4/6] 提交更改...
git commit -m "🎮 添加 XServer Game Server 自动续期功能

- 添加 Playwright 自动续期脚本
- 配置 GitHub Actions 工作流
- 添加完整文档和配置指南
- 支持 Telegram/邮件通知
- 智能续期判断（剩余 < 23 小时）"
echo.

REM 设置远程仓库
echo [5/6] 设置远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/phaip88/xserver-game-renewal.git
echo.

REM 推送到 GitHub
echo [6/6] 推送到 GitHub...
echo.

REM 检查环境变量
if defined GITHUB_TOKEN (
    echo ✅ 检测到环境变量 GITHUB_TOKEN
    echo 使用环境变量进行认证...
    echo.
    git push https://%GITHUB_TOKEN%@github.com/phaip88/xserver-game-renewal.git main
) else (
    echo ⚠️ 未检测到环境变量 GITHUB_TOKEN
    echo 请输入你的 GitHub Personal Access Token:
    echo.
    git push -u origin main
)
echo.

if %errorlevel% equ 0 (
    echo ========================================
    echo ✅ 推送成功！
    echo ========================================
    echo.
    echo 下一步：
    echo 1. 访问 https://github.com/phaip88/xserver-game-renewal
    echo 2. 进入 Settings → Secrets and variables → Actions
    echo 3. 添加以下 Secrets:
    echo    - XSERVER_EMAIL
    echo    - XSERVER_PASSWORD
    echo 4. 进入 Actions 标签页启用工作流
    echo 5. 手动运行一次测试
    echo.
) else (
    echo ========================================
    echo ❌ 推送失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 仓库不存在 - 请先在 GitHub 创建仓库
    echo 2. Token 权限不足 - 确保 token 有 repo 权限
    echo 3. 网络问题 - 检查网络连接
    echo.
)

pause
