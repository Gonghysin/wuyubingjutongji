from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from .models import Rating, User, Class
from . import db
from functools import wraps
import logging
import pandas as pd
import io
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile
from import_students import import_students

main = Blueprint('main', __name__)

# 配置上传文件存储
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def monitor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('main.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_monitor:
            flash('您没有班长权限', 'warning')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        
        user = User.query.filter_by(student_id=student_id).first()
        
        # 尝试普通密码登录
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_monitor'] = user.is_monitor
            if user.class_id:
                session['class_id'] = user.class_id
                class_obj = Class.query.get(user.class_id)
                if class_obj:
                    session['class_name'] = class_obj.name
            
            # 根据用户是否是班长来显示不同的成功消息
            if user.is_monitor:
                flash('班长登录成功！', 'success')
            else:
                flash('登录成功！', 'success')
            
            # 根据用户身份自动重定向到相应页面
            if user.is_monitor:
                return redirect(url_for('main.monitor_dashboard'))
            return redirect(url_for('main.index'))
        # 如果是班长，尝试使用班长专用密码登录
        elif user and user.is_monitor and user.check_monitor_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_monitor'] = True
            if user.class_id:
                session['class_id'] = user.class_id
                class_obj = Class.query.get(user.class_id)
                if class_obj:
                    session['class_name'] = class_obj.name
            
            flash('班长登录成功！', 'success')
            return redirect(url_for('main.monitor_dashboard'))
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
    
    # 如果用户没有班级，提示用户联系班长
    if not current_user.class_id:
        flash('您尚未被分配到班级，请联系班长', 'warning')
        return render_template('index.html', users=[], rated_student_ids=[], current_user=current_user, class_info=None)
    
    # 获取当前用户所在班级的所有用户
    users_to_rate = User.query.filter_by(class_id=current_user.class_id).all()
    
    # 获取当前用户已评分的学生ID列表
    rated_student_ids = db.session.query(Rating.rated_student_id).filter(
        Rating.student_id == current_user.id
    ).all()
    rated_student_ids = [r[0] for r in rated_student_ids]
    
    # 获取班级信息
    class_info = Class.query.get(current_user.class_id)
    
    return render_template('index.html', users=users_to_rate, rated_student_ids=rated_student_ids, current_user=current_user, class_info=class_info)

@main.route('/rate/<int:student_id>', methods=['GET', 'POST'])
@login_required
def rate(student_id):
    current_user = User.query.get(session['user_id'])
    rated_user = User.query.get_or_404(student_id)
    
    # 检查用户是否已锁定
    if current_user.locked:
        flash('您的评价已锁定，无法修改', 'warning')
        return redirect(url_for('main.index'))
    
    # 检查是否同一个班级
    if current_user.class_id != rated_user.class_id:
        flash('您只能给同班同学评分', 'warning')
        return redirect(url_for('main.index'))
    
    # 检查是否已经评分
    existing_rating = Rating.query.filter_by(
        student_id=current_user.id,
        rated_student_id=rated_user.id
    ).first()
    
    if request.method == 'POST':
        # 获取评分数据
        moral = request.form.get('moral')
        intelligence = request.form.get('intelligence')
        physical = request.form.get('physical')
        aesthetic = request.form.get('aesthetic')
        labor = request.form.get('labor')
        
        if existing_rating:
            # 更新现有评分
            existing_rating.moral = moral
            existing_rating.intelligence = intelligence
            existing_rating.physical = physical
            existing_rating.aesthetic = aesthetic
            existing_rating.labor = labor
            flash('评分已更新！', 'success')
        else:
            # 创建新评分
            rating = Rating(
                student_id=current_user.id,
                rated_student_id=rated_user.id,
                moral=moral,
                intelligence=intelligence,
                physical=physical,
                aesthetic=aesthetic,
                labor=labor
            )
            db.session.add(rating)
            flash('评分成功！', 'success')
        
        try:
            db.session.commit()
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"评分失败: {error_msg}")
            flash(f'评分失败: {error_msg}', 'error')
    
    return render_template('rate.html', student=rated_user, existing_rating=existing_rating, current_user=current_user)

@main.route('/lock_ratings')
@login_required
def lock_ratings():
    current_user = User.query.get(session['user_id'])
    
    # 检查是否已经锁定
    if current_user.locked:
        flash('您的评价已经锁定', 'warning')
        return redirect(url_for('main.index'))
    
    # 获取当前班级内需要评分的用户（除了自己）
    users_to_rate = User.query.filter(
        User.id != current_user.id,
        User.class_id == current_user.class_id
    ).all()
    
    # 检查是否已经完成班级内所有同学的评价
    for user in users_to_rate:
        rating = Rating.query.filter_by(
            student_id=current_user.id,
            rated_student_id=user.id
        ).first()
        if not rating:
            flash('您还未完成所有评价，无法锁定', 'warning')
            return redirect(url_for('main.index'))
    
    # 锁定评价
    current_user.locked = True
    try:
        db.session.commit()
        flash('评价已锁定，无法再修改', 'success')
    except Exception as e:
        db.session.rollback()
        flash('锁定失败，请重试', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/monitor/dashboard')
@login_required
@monitor_required
def monitor_dashboard():
    current_user = User.query.get(session['user_id'])
    
    # 获取班长管理的班级
    if current_user.class_id:
        class_info = Class.query.get(current_user.class_id)
        students = User.query.filter_by(class_id=current_user.class_id).all()
    else:
        class_info = None
        students = []
    
    # 统计未完成评分的学生
    incomplete_students = []
    for student in students:
        if not student.locked and student.id != current_user.id:  # 排除班长自己
            incomplete_students.append(student)
    
    return render_template('monitor_dashboard.html', 
                           class_info=class_info, 
                           students=students, 
                           incomplete_students=incomplete_students,
                           current_user=current_user)

@main.route('/monitor/upload_students', methods=['GET', 'POST'])
@login_required
@monitor_required
def upload_students():
    current_user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # 检查是否有文件
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            # 保存文件到临时目录
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # 导入学生名单
            if current_user.class_id:
                # 使用现有班级
                result = import_students(file_path, class_id=current_user.class_id)
            else:
                # 创建新班级
                class_name = request.form.get('class_name')
                if not class_name:
                    flash('请输入班级名称', 'error')
                    return redirect(request.url)
                    
                result = import_students(file_path, class_name=class_name)
                
                # 如果成功创建班级，将班长关联到该班级
                if result:
                    # 查找新创建的班级
                    new_class = Class.query.filter_by(name=class_name).first()
                    if new_class:
                        current_user.class_id = new_class.id
                        db.session.commit()
                        session['class_id'] = new_class.id
                        session['class_name'] = new_class.name
            
            # 删除临时文件
            os.remove(file_path)
            
            if result:
                flash('学生名单导入成功', 'success')
                return redirect(url_for('main.monitor_dashboard'))
            else:
                flash('学生名单导入失败', 'error')
    
    # 获取班长当前管理的班级
    class_info = None
    if current_user.class_id:
        class_info = Class.query.get(current_user.class_id)
    
    return render_template('upload_students.html', class_info=class_info, current_user=current_user)

@main.route('/results')
@login_required
def results():
    current_user = User.query.get(session['user_id'])
    
    # 如果用户没有班级，提示用户联系班长
    if not current_user.class_id:
        flash('您尚未被分配到班级，请联系班长', 'warning')
        return render_template('results.html', students=[], class_info=None)
    
    # 只获取当前用户所在班级的学生
    students = User.query.filter_by(class_id=current_user.class_id).all()
    
    # 获取班级信息
    class_info = Class.query.get(current_user.class_id)
    
    return render_template('results.html', students=students, class_info=class_info)

@main.route('/export_results')
@login_required
def export_results():
    current_user = User.query.get(session['user_id'])
    
    # 如果用户没有班级，提示用户联系班长
    if not current_user.class_id:
        flash('您尚未被分配到班级，请联系班长', 'warning')
        return redirect(url_for('main.results'))
    
    # 只获取当前用户所在班级的学生
    students = User.query.filter_by(class_id=current_user.class_id).all()
    
    # 获取班级信息
    class_info = Class.query.get(current_user.class_id)
    
    # 准备数据
    data = []
    for student in students:
        # 获取该学生的所有评分
        received_ratings = student.received_ratings
        
        # 统计各维度的评分
        dimensions = ['moral', 'intelligence', 'physical', 'aesthetic', 'labor']
        stats = {}
        
        for dim in dimensions:
            ratings = [getattr(r, dim) for r in received_ratings]
            if ratings:
                stats[dim] = {
                    'A': ratings.count('A'),
                    'B': ratings.count('B'),
                    'C': ratings.count('C'),
                    'D': ratings.count('D'),
                    'total': len(ratings)
                }
            else:
                stats[dim] = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'total': 0}
        
        # 添加到数据列表
        data.append({
            '学号': student.student_id,
            '姓名': student.name,
            '德育评分总数': stats['moral']['total'],
            '德育A': stats['moral']['A'],
            '德育B': stats['moral']['B'],
            '德育C': stats['moral']['C'],
            '德育D': stats['moral']['D'],
            '智育评分总数': stats['intelligence']['total'],
            '智育A': stats['intelligence']['A'],
            '智育B': stats['intelligence']['B'],
            '智育C': stats['intelligence']['C'],
            '智育D': stats['intelligence']['D'],
            '体育评分总数': stats['physical']['total'],
            '体育A': stats['physical']['A'],
            '体育B': stats['physical']['B'],
            '体育C': stats['physical']['C'],
            '体育D': stats['physical']['D'],
            '美育评分总数': stats['aesthetic']['total'],
            '美育A': stats['aesthetic']['A'],
            '美育B': stats['aesthetic']['B'],
            '美育C': stats['aesthetic']['C'],
            '美育D': stats['aesthetic']['D'],
            '劳动评分总数': stats['labor']['total'],
            '劳动A': stats['labor']['A'],
            '劳动B': stats['labor']['B'],
            '劳动C': stats['labor']['C'],
            '劳动D': stats['labor']['D']
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='评分统计')
    
    # 准备文件下载
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    class_name = class_info.name if class_info else '未知班级'
    filename = f'{class_name}_互评统计结果_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@main.route('/get_rating_details/<int:student_id>')
@login_required
def get_rating_details(student_id):
    current_user = User.query.get(session['user_id'])
    student = User.query.get_or_404(student_id)
    
    # 检查是否同一个班级
    if current_user.class_id != student.class_id:
        return jsonify({'error': '您只能查看同班同学的评分详情'}), 403
        
    received_ratings = student.received_ratings
    
    details = []
    for rating in received_ratings:
        rater = User.query.get(rating.student_id)
        details.append({
            'rater_name': rater.name,
            'rater_id': rater.student_id,
            'moral': rating.moral,
            'intelligence': rating.intelligence,
            'physical': rating.physical,
            'aesthetic': rating.aesthetic,
            'labor': rating.labor,
            'created_at': rating.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(details)

@main.route('/admin/clear_ratings/<int:student_id>', methods=['POST'])
@login_required
def clear_student_ratings(student_id):
    # 获取当前用户
    current_user = User.query.get(session['user_id'])
    
    # 获取要清除评分的学生
    student = User.query.get_or_404(student_id)
    
    # 检查权限 - 只有学生所在班级的班长才能清除评分
    if not current_user.is_monitor or (current_user.is_monitor and current_user.class_id != student.class_id):
        return jsonify({'message': '您没有权限执行此操作'}), 403
    
    try:
        # 查找该学生提交的所有评分
        ratings = Rating.query.filter_by(student_id=student_id).all()
        
        if not ratings:
            return jsonify({'message': f'该学生（{student.name}）没有提交任何评分记录'}), 404
        
        # 删除评分记录
        count = 0
        for rating in ratings:
            db.session.delete(rating)
            count += 1
        
        # 解锁该学生的评分状态
        student.locked = False
        
        db.session.commit()
        
        # 返回成功消息
        return jsonify({'message': f'成功清除 {student.name} 提交的 {count} 条评分记录，并已解锁评分状态', 'count': count})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"清除评分失败: {str(e)}")
        return jsonify({'message': f'清除评分失败: {str(e)}'}), 500

@main.route('/admin/unlock_student/<int:student_id>', methods=['POST'])
@login_required
def unlock_student(student_id):
    # 获取当前用户
    current_user = User.query.get(session['user_id'])
    
    # 获取要解锁的学生
    student = User.query.get_or_404(student_id)
    
    # 检查权限 - 只有管理员或学生所在班级的班长才能解锁
    if not current_user.is_monitor or (current_user.is_monitor and current_user.class_id != student.class_id):
        return jsonify({'message': '您没有权限执行此操作'}), 403
    
    try:
        # 检查学生是否已经解锁
        if not student.locked:
            return jsonify({'message': f'该学生（{student.name}）的评分未锁定'}), 400
        
        # 解锁学生评分
        student.locked = False
        db.session.commit()
        
        # 返回成功消息
        return jsonify({'message': f'已成功解锁 {student.name} 的评分状态'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"解锁失败: {str(e)}")
        return jsonify({'message': f'解锁失败: {str(e)}'}), 500
        
@main.route('/admin/set_monitor/<int:student_id>', methods=['POST'])
@login_required
def set_monitor(student_id):
    # 获取当前用户（应该是管理员）
    current_user = User.query.get(session['user_id'])
    
    # 获取要设置为班长的学生
    student = User.query.get_or_404(student_id)
    
    try:
        # 设置为班长
        student.is_monitor = True
        db.session.commit()
        
        # 返回成功消息
        return jsonify({'message': f'已成功将 {student.name} 设置为班长'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"设置班长失败: {str(e)}")
        return jsonify({'message': f'设置班长失败: {str(e)}'}), 500