#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 打包脚本"""

import os
import sys
import shutil
import subprocess

def build():
    """打包成EXE"""
    print("=" * 50)
    print("  试卷管理系统 - 打包工具")
    print("=" * 50)
    print()
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("[✓] PyInstaller 已安装")
    except ImportError:
        print("[!] 正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("[✓] PyInstaller 安装完成")
    
    # 清理旧的构建文件
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[✓] 清理 {dir_name} 目录")
    
    # 创建数据目录
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads/exams', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # PyInstaller 参数
    args = [
        'pyinstaller',
        '--name=试卷管理系统',
        '--onedir',  # 打包成目录（比单文件启动更快）
        '--windowed',  # 不显示控制台窗口
        '--icon=NONE',
        '--add-data=templates;templates',
        '--add-data=data;data',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=markupsafe',
        '--hidden-import=requests',
        '--hidden-import=sqlite3',
        '--hidden-import=json',
        '--hidden-import=datetime',
        '--hidden-import=threading',
        '--hidden-import=traceback',
        '--hidden-import=base64',
        '--hidden-import=io',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--noconfirm',
        '--clean',
        'app.py'
    ]
    
    print()
    print("[*] 开始打包...")
    print()
    
    # 执行打包
    result = subprocess.run(args, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[✓] 打包成功！")
        print()
        print(f"输出目录: {os.path.abspath('dist/试卷管理系统')}")
        print()
        
        # 创建启动脚本
        launcher_path = os.path.join('dist', '试卷管理系统', '启动.bat')
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('chcp 65001 >nul\n')
            f.write('cd /d "%~dp0"\n')
            f.write('start "" "试卷管理系统.exe"\n')
        
        # 复制数据目录模板
        for dir_name in ['data', 'uploads', 'logs']:
            target_dir = os.path.join('dist', '试卷管理系统', dir_name)
            os.makedirs(target_dir, exist_ok=True)
        
        print("[✓] 已创建启动脚本和数据目录")
        print()
        print("=" * 50)
        print("  打包完成！")
        print("=" * 50)
        print()
        print("使用方法:")
        print("1. 将 dist/试卷管理系统 目录复制到目标机器")
        print("2. 双击 运行.bat 启动程序")
        print("3. 访问 http://localhost:5001")
        print()
        
        # 创建ZIP压缩包
        try:
            import zipfile
            zip_path = 'dist/试卷管理系统.zip'
            print("[*] 正在创建压缩包...")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk('dist/试卷管理系统'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, 'dist')
                        zipf.write(file_path, arcname)
            
            print(f"[✓] 压缩包已创建: {zip_path}")
        except Exception as e:
            print(f"[!] 创建压缩包失败: {e}")
        
    else:
        print("[✗] 打包失败！")
        print()
        print("错误信息:")
        print(result.stderr)
        print()
        print("可能的原因:")
        print("1. 缺少依赖包")
        print("2. 文件路径包含特殊字符")
        print("3. 权限不足")
        print()
        print("建议:")
        print("1. 以管理员身份运行")
        print("2. 使用英文路径")
        print("3. 手动安装: pip install pyinstaller")

def create_portable_version():
    """创建便携版"""
    print()
    print("=" * 50)
    print("  创建便携版")
    print("=" * 50)
    print()
    
    portable_dir = 'dist/试卷管理系统-便携版'
    
    # 创建目录结构
    dirs = [
        portable_dir,
        f'{portable_dir}/data',
        f'{portable_dir}/uploads/exams',
        f'{portable_dir}/logs',
        f'{portable_dir}/templates',
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # 复制源代码
    source_files = [
        'app.py',
        'database.py',
        'ai_analyzer.py',
        'exam_recognizer.py',
        'storage.py',
        'cache.py',
        'requirements.txt',
    ]
    
    for f in source_files:
        if os.path.exists(f):
            shutil.copy2(f, portable_dir)
            print(f"[✓] 复制 {f}")
    
    # 复制模板目录
    if os.path.exists('templates'):
        shutil.copytree('templates', f'{portable_dir}/templates', dirs_exist_ok=True)
        print("[✓] 复制 templates 目录")
    
    # 创建启动脚本
    with open(f'{portable_dir}/安装依赖.bat', 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('chcp 65001 >nul\n')
        f.write('echo 安装依赖...\n')
        f.write('pip install -r requirements.txt\n')
        f.write('echo.\n')
        f.write('echo 安装完成！\n')
        f.write('pause\n')
    
    with open(f'{portable_dir}/启动系统.bat', 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('chcp 65001 >nul\n')
        f.write('cd /d "%~dp0"\n')
        f.write('echo ========================================\n')
        f.write('echo   试卷管理系统\n')
        f.write('echo ========================================\n')
        f.write('echo.\n')
        f.write('echo 访问地址: http://localhost:5001\n')
        f.write('echo 默认账号: admin / admin123\n')
        f.write('echo.\n')
        f.write('python app.py\n')
        f.write('pause\n')
    
    # 创建README
    with open(f'{portable_dir}/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write('试卷管理系统 - 便携版\n')
        f.write('=' * 40 + '\n\n')
        f.write('使用方法:\n')
        f.write('1. 双击 "安装依赖.bat" 安装Python依赖\n')
        f.write('2. 双击 "启动系统.bat" 启动程序\n')
        f.write('3. 浏览器访问 http://localhost:5001\n')
        f.write('4. 默认管理员账号: admin / admin123\n\n')
        f.write('系统要求:\n')
        f.write('- Windows 10/11\n')
        f.write('- Python 3.8+\n')
        f.write('- 2GB+ 磁盘空间\n')
    
    print()
    print(f"[✓] 便携版已创建: {portable_dir}")
    print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--portable':
        create_portable_version()
    else:
        build()
    
    input("\n按回车键退出...")
