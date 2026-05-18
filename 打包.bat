@echo off
chcp 65001 >nul
echo ========================================
echo   试卷管理系统 - 完整打包工具
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)
echo [✓] Python已安装

echo.
echo [2/5] 安装打包工具...
pip install pyinstaller -q
echo [✓] PyInstaller已安装

echo.
echo [3/5] 创建打包目录...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
mkdir dist\试卷管理系统
mkdir dist\试卷管理系统\data
mkdir dist\试卷管理系统\uploads\exams
mkdir dist\试卷管理系统\logs
mkdir dist\试卷管理系统\templates

echo.
echo [4/5] 复制必要文件...
xcopy /E /I /Y templates dist\试卷管理系统\templates >nul
copy /Y *.py dist\试卷管理系统\ >nul
copy /Y requirements.txt dist\试卷管理系统\ >nul
echo [✓] 文件复制完成

echo.
echo [5/5] 创建启动脚本...

REM 创建启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%%~dp0"
echo echo ========================================
echo echo   试卷管理系统 v1.9
echo echo ========================================
echo echo.
echo echo 正在启动服务...
echo echo 访问地址: http://localhost:5001
echo echo 默认账号: admin / admin123
echo echo.
echo echo 按 Ctrl+C 停止服务
echo echo ========================================
echo python app.py
) > dist\试卷管理系统\启动系统.bat

REM 创建安装依赖脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo   安装依赖
echo echo ========================================
echo echo.
echo pip install flask^>=2.0.0
echo pip install requests^>=2.28.0
echo pip install werkzeug^>=2.0.0
echo pip install PyMuPDF
echo pip install PyPDF2
echo pip install python-docx
echo pip install pillow
echo pip install pytesseract
echo echo.
echo echo [✓] 依赖安装完成！
echo pause
) > dist\试卷管理系统\安装依赖.bat

REM 创建使用说明
(
echo 试卷管理系统 v1.9
echo ========================================
echo.
echo 安装步骤:
echo 1. 确保已安装 Python 3.8+
echo 2. 双击 "安装依赖.bat" 安装依赖包
echo 3. 双击 "启动系统.bat" 启动程序
echo 4. 浏览器访问 http://localhost:5001
echo.
echo 默认账号: admin / admin123
echo.
echo 目录说明:
echo - data: 数据库文件
echo - uploads: 上传的试卷
echo - logs: 日志文件
echo.
echo 备份说明:
echo 备份 data/exam_system.db 即可保存所有数据
) > dist\试卷管理系统\使用说明.txt

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 输出目录: dist\试卷管理系统
echo.
echo 使用方法:
echo 1. 将 dist\试卷管理系统 目录打包成ZIP
echo 2. 在目标机器解压
echo 3. 运行 "安装依赖.bat"
echo 4. 运行 "启动系统.bat"
echo.

REM 创建ZIP压缩包
echo [*] 正在创建压缩包...
powershell -Command "Compress-Archive -Path 'dist\试卷管理系统' -DestinationPath 'dist\试卷管理系统.zip' -Force"
if exist "dist\试卷管理系统.zip" (
    echo [✓] 压缩包已创建: dist\试卷管理系统.zip
) else (
    echo [!] 压缩包创建失败，请手动压缩 dist\试卷管理系统 目录
)

echo.
echo ========================================
echo   全部完成！
echo ========================================
echo.
pause
