from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    students = db.relationship('User', backref='class_', lazy='dynamic')
    
    def __repr__(self):
        return f'<Class {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locked = db.Column(db.Boolean, default=False)  # 添加锁定状态字段
    is_monitor = db.Column(db.Boolean, default=False)  # 是否为班长
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))  # 关联到班级
    
    # 关系
    self_ratings = db.relationship('Rating', backref='student', foreign_keys='Rating.student_id')
    received_ratings = db.relationship('Rating', backref='rated_student', foreign_keys='Rating.rated_student_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def check_monitor_password(self, password):
        """班长身份验证方法，使用学号后5位作为管理密码
        
        Args:
            password: 输入的密码
            
        Returns:
            bool: 密码是否正确
        """
        if not self.is_monitor:
            return False
            
        # 使用学号后5位作为管理密码
        monitor_password = self.student_id[-5:]
        return password == monitor_password

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    moral = db.Column(db.String(1), nullable=False)  # A, B, C, D
    intelligence = db.Column(db.String(1), nullable=False)
    physical = db.Column(db.String(1), nullable=False)
    aesthetic = db.Column(db.String(1), nullable=False)
    labor = db.Column(db.String(1), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 确保每个学生只能给同一个同学评分一次
    __table_args__ = (
        db.UniqueConstraint('student_id', 'rated_student_id', name='unique_rating'),
    )