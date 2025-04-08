from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import db, Rating, User
from functools import wraps

main = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        user = User.query.filter_by(student_id=student_id).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('登录成功！', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('学号或密码错误', 'error')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('main.login'))

@main.route('/')
@login_required
def index():
    current_user = User.query.get(session['user_id'])
    # 获取所有需要评分的用户（除了自己）
    users_to_rate = User.query.filter(User.id != current_user.id).all()
    return render_template('index.html', users=users_to_rate)

@main.route('/rate/<int:student_id>', methods=['GET', 'POST'])
@login_required
def rate(student_id):
    if request.method == 'POST':
        current_user = User.query.get(session['user_id'])
        rated_user = User.query.get_or_404(student_id)
        
        # 获取评分数据
        moral = request.form.get('moral')
        intelligence = request.form.get('intelligence')
        physical = request.form.get('physical')
        aesthetic = request.form.get('aesthetic')
        labor = request.form.get('labor')
        
        # 创建评分记录
        rating = Rating(
            student_id=current_user.id,
            rated_student_id=rated_user.id,
            moral=moral,
            intelligence=intelligence,
            physical=physical,
            aesthetic=aesthetic,
            labor=labor
        )
        
        try:
            db.session.add(rating)
            db.session.commit()
            flash('评分成功！', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash('评分失败，请重试！', 'error')
    
    rated_user = User.query.get_or_404(student_id)
    return render_template('rate.html', student=rated_user)

@main.route('/results')
@login_required
def results():
    users = User.query.all()
    return render_template('results.html', users=users) 