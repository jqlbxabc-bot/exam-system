# 试卷管理系统 v1.9

## 安装说明

### 方式一：快速安装（推荐）

1. 确保已安装 Python 3.8+
2. 双击运行 `安装.bat`
3. 双击 `启动试卷管理系统.bat` 启动程序
4. 访问 http://localhost:5001

### 方式二：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python -c "import database; database.init_db()"

# 3. 启动程序
python app.py
```

### 方式三：打包成EXE

```bash
# 1. 安装打包工具
pip install pyinstaller

# 2. 运行打包脚本
python build.py
```

打包完成后在 `dist` 目录生成 `试卷管理系统.exe`

## 系统要求

- Windows 10/11
- Python 3.8+
- 2GB+ 磁盘空间

## 默认账号

- 管理员：admin / admin123

## 云端 AI 默认配置

部署到 Railway、Docker、云服务器等环境时，请设置环境变量：

```bash
AI_PROVIDER=deepseek
AI_API_KEY=你的DeepSeek API Key
AI_MODEL=deepseek-v4-flash
AI_BASE_URL=https://api.deepseek.com
```

程序启动时会自动读取这些变量并写入系统配置；网页端无需再次手动填写 API 配置。

## 功能特性

- 试卷管理（上传/编辑/预览/搜索）
- AI智能分析（5种策略，7种AI provider）
- 错题本（自动/手动添加，掌握度追踪）
- 专项练习（AI出题 + 高考真题匹配）
- 改错管理（多次改错跟踪）
- 高考真题库（AI自动分类，树形浏览）
- 学习统计（成绩趋势图表）
- 学习计划（任务管理，进度跟踪）
- 复习提醒（艾宾浩斯遗忘曲线）

## 目录结构

```
试卷管理系统/
├── app.py              # 主程序
├── database.py         # 数据库模块
├── ai_analyzer.py      # AI分析模块
├── exam_recognizer.py  # 试卷识别模块
├── storage.py          # 存储模块
├── cache.py            # 缓存模块
├── requirements.txt    # 依赖列表
├── 安装.bat            # 安装脚本
├── 启动试卷管理系统.bat # 启动脚本
├── data/               # 数据库目录
├── uploads/            # 上传文件目录
└── templates/          # 模板文件
```

## 常见问题

### Q: 启动时报错"No module named xxx"
A: 运行 `pip install -r requirements.txt` 安装依赖

### Q: 端口5001被占用
A: 修改 app.py 最后一行的端口号

### Q: 如何备份数据
A: 复制 `data/exam_system.db` 文件

## 技术支持

- 问题反馈：请提交Issue
- 文档：查看 开发文档.md
