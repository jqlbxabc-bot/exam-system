@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   试卷管理系统 v1.9
echo ========================================
echo.
echo 访问地址: http://localhost:5001
echo 默认账号: admin / admin123
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python app.py
pause
