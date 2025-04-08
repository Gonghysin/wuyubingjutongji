from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from .models import Rating, User
from . import db
from functools import wraps
import logging
import pandas as pd
import io
from datetime import datetime

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
    # 获取所有用户（包括自己）
    users_to_rate = User.query.all()
    
    # 获取当前用户已评分的学生ID列表
    rated_student_ids = db.session.query(Rating.rated_student_id).filter(
        Rating.student_id == current_user.id
    ).all()
    rated_student_ids = [r[0] for r in rated_student_ids]
    
    return render_template('index.html', users=users_to_rate, rated_student_ids=rated_student_ids, current_user=current_user)

@main.route('/rate/<int:student_id>', methods=['GET', 'POST'])
@login_required
def rate(student_id):
    current_user = User.query.get(session['user_id'])
    rated_user = User.query.get_or_404(student_id)
    
    # 检查用户是否已锁定
    if current_user.locked:
        flash('您的评价已锁定，无法修改', 'warning')
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
    
    # 获取所有需要评分的用户（除了自己）
    users_to_rate = User.query.filter(User.id != current_user.id).all()
    
    # 检查是否已经完成所有评价
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

@main.route('/results')
@login_required
def results():
    students = User.query.all()
    return render_template('results.html', students=students)

@main.route('/export_results')
@login_required
def export_results():
    # 获取所有学生
    students = User.query.all()
    
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
    filename = f'班级互评统计结果_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@main.route('/get_rating_details/<int:student_id>')
@login_required
def get_rating_details(student_id):
    student = User.query.get_or_404(student_id)
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
    # 获取要清除评分的学生
    student = User.query.get_or_404(student_id)
    
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