# 五育并举统计系统

这是一个基于Flask的学生互评系统，用于实现学生之间的德智体美劳五维度评价统计。

## 主要功能

- 用户认证：学生可以使用学号和密码登录系统
- 互评功能：学生可以对其他同学进行德智体美劳五个维度的评分（A/B/C/D）
- 评分管理：支持评分的修改和锁定功能
- 数据导出：管理员可以导出评分数据进行统计分析

## 技术栈

### 后端
- Flask 2.0.1：Python Web框架
- SQLAlchemy 1.4.23：ORM框架
- Flask-SQLAlchemy 2.5.1：Flask的SQLAlchemy扩展
- Werkzeug 2.0.1：WSGI工具库

### 数据处理
- NumPy 1.21.0：数值计算库
- Pandas 1.3.3：数据分析库
- OpenPyXL 3.0.9：Excel文件处理

### 前端
- HTML/CSS/JavaScript：基础前端技术
- Bootstrap：响应式UI框架

## 安装和运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 初始化数据库：
```bash
flask db upgrade
```

3. 运行应用：
```bash
python run.py
```

## 项目结构

```
.
├── app/                # 应用主目录
│   ├── __init__.py    # 应用初始化
│   ├── models.py      # 数据模型
│   ├── routes.py      # 路由处理
│   ├── static/        # 静态文件
│   └── templates/     # HTML模板
├── migrations/        # 数据库迁移文件
├── docs/             # 项目文档
├── requirements.txt   # 项目依赖
└── run.py            # 应用入口
```