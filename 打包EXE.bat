@echo off
chcp 65001 >nul
echo ========================================
echo   试卷管理系统 - 一键打包EXE
echo ========================================
echo.

echo [1/6] 检查环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)
echo [✓] Python已安装

echo.
echo [2/6] 安装打包工具...
pip install pyinstaller -q
pip install flask -q
pip install requests -q
pip install PyMuPDF -q
pip install PyPDF2 -q
pip install python-docx -q
pip install pillow -q
echo [✓] 依赖安装完成

echo.
echo [3/6] 清理旧文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo [✓] 清理完成

echo.
echo [4/6] 创建数据目录...
mkdir data 2>nul
mkdir uploads\exams 2>nul
mkdir logs 2>nul
echo [✓] 目录创建完成

echo.
echo [5/6] 开始打包EXE...
echo 这可能需要几分钟，请耐心等待...
echo.

pyinstaller ^
    --name="试卷管理系统" ^
    --onedir ^
    --noconsole ^
    --add-data="templates;templates" ^
    --add-data="data;data" ^
    --hidden-import=flask ^
    --hidden-import=werkzeug ^
    --hidden-import=jinja2 ^
    --hidden-import=markupsafe ^
    --hidden-import=requests ^
    --hidden-import=sqlite3 ^
    --hidden-import=json ^
    --hidden-import=datetime ^
    --hidden-import=threading ^
    --hidden-import=traceback ^
    --hidden-import=base64 ^
    --hidden-import=io ^
    --hidden-import=os ^
    --hidden-import=sys ^
    --hidden-import=PyMuPDF ^
    --hidden-import=fitz ^
    --hidden-import=PyPDF2 ^
    --hidden-import=docx ^
    --hidden-import=PIL ^
    --noconfirm ^
    --clean ^
    app.py

if errorlevel 1 (
    echo.
    echo [✗] 打包失败！
    echo 可能原因：
    echo 1. 缺少依赖包
    echo 2. 文件路径问题
    echo 3. 权限不足
    pause
    exit /b 1
)

echo.
echo [6/6] 完善打包内容...

REM 复制额外文件到打包目录
copy /Y requirements.txt "dist\试卷管理系统\" >nul 2>&1
copy /Y README.md "dist\试卷管理系统\" >nul 2>&1

REM 创建数据目录
mkdir "dist\试卷管理系统\data" 2>nul
mkdir "dist\试卷管理系统\uploads" 2>nul
mkdir "dist\试卷管理系统\uploads\exams" 2>nul
mkdir "dist\试卷管理系统\logs" 2>nul

REM 创建启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%%~dp0"
echo echo ========================================
echo echo   试卷管理系统 v1.9
echo echo ========================================
echo echo.
echo echo 访问地址: http://localhost:5001
echo echo 默认账号: admin / admin123
echo echo.
echo echo 按 Ctrl+C 停止服务
echo echo ========================================
echo start "" "试卷管理系统.exe"
echo pause
) > "dist\试卷管理系统\启动系统.bat"

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 输出目录: dist\试卷管理系统
echo.
echo 使用方法:
echo 1. 将 "dist\试卷管理系统" 目录复制到目标机器
echo 2. 双击 "启动系统.bat" 或 "试卷管理系统.exe"
echo 3. 浏览器访问 http://localhost:5001
echo.

REM 创建压缩包
echo [*] 正在创建压缩包...
powershell -Command "Compress-Archive -Path 'dist\试卷管理系统' -DestinationPath 'dist\试卷管理系统-安装包.zip' -Force" 2>nul
if exist "dist\试卷管理系统-安装包.zip" (
    echo [✓] 压缩包已创建: dist\试卷管理系统-安装包.zip
) else (
    echo [!] 请手动压缩 dist\试卷管理系统 目录
)

echo.
echo ========================================
echo   全部完成！
echo ========================================
echo.
pause
