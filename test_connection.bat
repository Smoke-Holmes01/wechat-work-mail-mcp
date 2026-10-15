@echo off
chcp 65001 > nul
echo ========================================================
echo   企业微信邮箱连通性自测工具
echo ========================================================
echo.

if not exist ".\.venv\Scripts\python.exe" (
    echo [提示] 尚未检测到虚拟环境，请先双击运行 install.bat 进行初始化安装！
    echo.
    pause
    exit /b 1
)

echo 正在连接腾讯企业邮箱服务器测试连通性与账号有效性...
echo.

.\.venv\Scripts\python.exe -c "from wechat_work_mail.server import exmail_check_connection; import json; res = exmail_check_connection(); print(json.dumps(res, ensure_ascii=False, indent=2))"

echo.
echo ========================================================
pause
