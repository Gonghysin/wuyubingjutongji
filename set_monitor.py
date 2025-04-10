from app import create_app, db
from app.models import User
import argparse

def set_monitor(student_id):
    """将指定学号的学生设置为班长
    
    Args:
        student_id: 学生学号
    """
    app = create_app()
    with app.app_context():
        # 查找学生
        student = User.query.filter_by(student_id=student_id).first()
        
        if not student:
            print(f"错误: 学号为 {student_id} 的学生不存在")
            return False
        
        # 设置为班长
        student.is_monitor = True
        
        try:
            db.session.commit()
            monitor_password = student.student_id[-5:]
            print(f"成功: 已将 {student.name} (学号: {student.student_id}) 设置为班长")
            print(f"班长管理密码: {monitor_password} (学号后5位)")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"错误: 设置班长失败 - {str(e)}")
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='设置班长')
    parser.add_argument('student_id', help='要设置为班长的学生学号')
    
    args = parser.parse_args()
    
    set_monitor(args.student_id)