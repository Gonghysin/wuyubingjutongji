from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # 获取项目根目录的绝对路径
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "class_rating.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 注册蓝图
    from .routes import main
    app.register_blueprint(main)
    
    # 确保所有的模型都被导入
    from . import models
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app 