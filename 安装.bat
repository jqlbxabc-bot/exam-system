@echo off
chcp 65001 >nul
echo ========================================
echo   试卷管理系统 - 安装程序
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 创建目录结构...
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "uploads\exams" mkdir uploads\exams
if not exist "logs" mkdir logs

echo [2/4] 安装依赖包...
pip install flask>=2.0.0 -q
pip install requests>=2.28.0 -q
pip install werkzeug>=2.0.0 -q
pip install PyMuPDF -q
pip install PyPDF2 -q
pip install python-docx -q
pip install pillow -q
pip install pytesseract -q

echo [3/4] 初始化数据库...
python -c "import database; database.init_db()"

echo [4/4] 创建快捷方式...
echo @echo off > 启动试卷管理系统.bat
echo chcp 65001 ^>nul >> 启动试卷管理系统.bat
echo cd /d "%%~dp0" >> 启动试卷管理系统.bat
echo echo ======================================== >> 启动试卷管理系统.bat
echo echo   试卷管理系统 v1.9 >> 启动试卷管理系统.bat
echo echo ======================================== >> 启动试卷管理系统.bat
echo echo. >> 启动试卷管理系统.bat
echo echo 访问地址: http://localhost:5001 >> 启动试卷管理系统.bat
echo echo 默认账号: admin / admin123 >> 启动试卷管理系统.bat
echo echo. >> 启动试卷管理系统.bat
echo echo 按 Ctrl+C 停止服务 >> 启动试卷管理系统.bat
echo echo ======================================== >> 启动试卷管理系统.bat
echo python app.py >> 启动试卷管理系统.bat

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 双击 "启动试卷管理系统.bat" 启动程序
echo 访问地址: http://localhost:5001
echo 默认账号: admin / admin123
echo.
pause
