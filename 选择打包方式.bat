@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   试卷管理系统 - 打包工具集
echo ========================================
echo.
echo 请选择打包方式:
echo.
echo [1] 快速打包（完整目录包）
echo     - 包含源代码
echo     - 需要目标机器安装Python
echo     - 体积小，启动快
echo.
echo [2] 打包成EXE（单文件可执行）
echo     - 无需安装Python
echo     - 体积较大
echo     - 双击即可运行
echo.
echo [3] 创建便携版
echo     - 包含详细说明
echo     - 适合分享给他人
echo.
echo [0] 退出
echo.
echo ========================================

set /p choice=请输入选择 (0-3): 

if "%choice%"=="1" goto quick_pack
if "%choice%"=="2" goto exe_pack
if "%choice%"=="3" goto portable
if "%choice%"=="0" goto exit
echo 无效选择，请重新运行
pause
exit

:quick_pack
echo.
echo [*] 开始快速打包...
call 打包.bat
goto end

:exe_pack
echo.
echo [*] 开始打包EXE...
call 打包EXE.bat
goto end

:portable
echo.
echo [*] 创建便携版...
python build.py --portable
goto end

:exit
exit

:end
echo.
echo 打包完成！
pause
