@echo off
chcp 65001 > nul
echo ========================================================
echo   企业微信邮箱 (腾讯企业邮) MCP 服务一键安装配置
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境！
    echo 请先下载并安装 Python (>= 3.10)，且在安装时务必勾选 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

echo [1/2] 正在创建独立虚拟环境 (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [错误] 创建虚拟环境失败。
    pause
    exit /b 1
)

echo [2/2] 正在安装依赖包...
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接后重试。
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   恭喜！环境与依赖已成功安装完成！
echo.
echo   后续使用说明：
echo   1. 请查阅【使用指南.md】获取“客户端专用密码”；
echo   2. 将账号与密码配置到 AI 客户端 (Claude / Cursor / Antigravity)；
echo   3. 双击运行 test_connection.bat 可快速验证邮箱连通性。
echo ========================================================
echo.
pause
