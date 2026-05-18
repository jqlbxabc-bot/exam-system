@echo off
chcp 65001 >nul
echo ========================================
echo   推送代码到GitHub
echo ========================================
echo.

set /p username=请输入你的GitHub用户名: 

if "%username%"=="" (
    echo 用户名不能为空！
    pause
    exit /b 1
)

echo.
echo [*] 添加远程仓库...
git remote add origin https://github.com/%username%/exam-system.git 2>nul || git remote set-url origin https://github.com/%username%/exam-system.git

echo [*] 推送代码...
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo 推送失败！可能需要输入GitHub Personal Access Token
    echo.
    echo 获取Token方法：
    echo 1. 打开 https://github.com/settings/tokens
    echo 2. 点击 "Generate new token (classic)"
    echo 3. 勾选 "repo" 权限
    echo 4. 生成后复制token
    echo.
    echo 然后重新运行此脚本，在密码处粘贴Token
    pause
    exit /b 1
)

echo.
echo ========================================
echo   推送成功！
echo ========================================
echo.
echo 接下来请：
echo 1. 打开 https://railway.app
echo 2. 用GitHub登录
echo 3. New Project - Deploy from GitHub repo
echo 4. 选择 exam-system 仓库
echo.
pause
