# Railway 部署步骤

## 准备工作已完成 ✓

- Git仓库已初始化
- 代码已提交
- Procfile已配置
- requirements.txt已更新

## 接下来的步骤

### 第一步：创建GitHub仓库

1. 打开 https://github.com/new
2. 仓库名填写：`exam-system`
3. 选择 **Public**（免费）或 Private
4. 点击 **Create repository**

### 第二步：推送代码到GitHub

在命令行执行以下命令（替换 `你的用户名` 为你的GitHub用户名）：

```bash
cd C:\Users\jqlbx\Desktop\试卷管理系统
git remote add origin https://github.com/你的用户名/exam-system.git
git branch -M main
git push -u origin main
```

如果提示输入密码，需要使用 **Personal Access Token**：
1. 打开 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 勾选 **repo** 权限
4. 生成后复制token，粘贴为密码

### 第三步：部署到Railway

1. 打开 https://railway.app
2. 点击 **Login with GitHub**
3. 授权Railway访问你的GitHub
4. 点击 **New Project**
5. 选择 **Deploy from GitHub repo**
6. 选择 `exam-system` 仓库
7. 点击 **Deploy Now**
8. 等待部署完成（约2-3分钟）

### 第四步：配置环境变量（可选）

在Railway项目设置中添加：
- `SECRET_KEY`: 你的密钥（随机字符串）

### 第五步：访问应用

1. 部署完成后，点击 **Settings**
2. 在 **Domains** 部分点击 **Generate Domain**
3. 获得类似 `exam-system.up.railway.app` 的域名
4. 打开该域名即可访问

## 默认账号

- 用户名：admin
- 密码：admin123

## 注意事项

1. Railway免费额度：每月 $5（约500小时运行时间）
2. 数据存储在容器内，重启会丢失数据
3. 如需持久化存储，需要使用Railway的数据库服务

## 如需帮助

- Railway文档：https://docs.railway.app
- 遇到问题可查看Railway的Build Logs
