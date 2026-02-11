@echo off
chcp 65001 >nul
echo ========================================
echo 设置 GitHub Token 环境变量
echo ========================================
echo.
echo 这个脚本会帮你设置 GITHUB_TOKEN 环境变量
echo.
echo ⚠️ 重要提示：
echo 1. 先去 https://github.com/settings/tokens 生成新 Token
echo 2. 权限选择: repo (完整权限)
echo 3. 复制生成的 Token
echo.
echo ========================================
echo.

REM 提示用户选择
echo 请选择设置方式：
echo.
echo [1] 临时设置 (仅当前命令行窗口有效)
echo [2] 永久设置 (系统环境变量，所有窗口有效)
echo [3] 查看当前设置
echo [4] 删除环境变量
echo.
set /p choice="请输入选项 (1-4): "
echo.

if "%choice%"=="1" goto temp_set
if "%choice%"=="2" goto permanent_set
if "%choice%"=="3" goto view_token
if "%choice%"=="4" goto delete_token
goto invalid_choice

:temp_set
echo ========================================
echo 临时设置 GITHUB_TOKEN
echo ========================================
echo.
set /p token="请粘贴你的 GitHub Token: "
set GITHUB_TOKEN=%token%
echo.
echo ✅ 临时环境变量已设置！
echo.
echo 注意：
echo - 仅在当前命令行窗口有效
echo - 关闭窗口后失效
echo - 现在可以运行 push_to_github.bat
echo.
goto end

:permanent_set
echo ========================================
echo 永久设置 GITHUB_TOKEN
echo ========================================
echo.
set /p token="请粘贴你的 GitHub Token: "
echo.
echo 正在设置系统环境变量...
setx GITHUB_TOKEN "%token%"
echo.
if %errorlevel% equ 0 (
    echo ✅ 永久环境变量已设置！
    echo.
    echo 注意：
    echo - 需要重新打开命令行窗口才能生效
    echo - 所有新窗口都可以使用
    echo - 请关闭当前窗口，重新打开后运行 push_to_github.bat
    echo.
) else (
    echo ❌ 设置失败，可能需要管理员权限
    echo.
    echo 解决方案：
    echo 1. 右键点击此脚本，选择"以管理员身份运行"
    echo 2. 或使用临时设置方式 (选项 1)
    echo.
)
goto end

:view_token
echo ========================================
echo 查看当前 GITHUB_TOKEN 设置
echo ========================================
echo.
if defined GITHUB_TOKEN (
    echo ✅ GITHUB_TOKEN 已设置
    echo.
    echo Token 前缀: %GITHUB_TOKEN:~0,10%...
    echo Token 长度: 
    echo %GITHUB_TOKEN% | find /c /v ""
    echo.
) else (
    echo ❌ GITHUB_TOKEN 未设置
    echo.
    echo 请先运行选项 1 或 2 设置 Token
    echo.
)
goto end

:delete_token
echo ========================================
echo 删除 GITHUB_TOKEN 环境变量
echo ========================================
echo.
set /p confirm="确认删除? (Y/N): "
if /i not "%confirm%"=="Y" goto end
echo.
echo 正在删除...
set GITHUB_TOKEN=
setx GITHUB_TOKEN ""
echo.
echo ✅ 环境变量已删除
echo.
goto end

:invalid_choice
echo ❌ 无效选项，请重新运行脚本
echo.
goto end

:end
echo ========================================
pause
