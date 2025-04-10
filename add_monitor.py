from app import create_app, db
from app.models import User, Class
import argparse

def add_monitor(name, student_id, class_name):
    """添加学生到数据库并将其设置为班长
    
    Args:
        name: 学生姓名
        student_id: 学生学号
        class_name: 班级名称
    
    Returns:
        bool: 操作是否成功
    """
    app = create_app()
    with app.app_context():
        # 检查学生是否已存在
        existing_student = User.query.filter_by(student_id=student_id).first()
        if existing_student:
            print(f"警告: 学号为 {student_id} 的学生已存在")
            # 如果已经是班长，直接返回
            if existing_student.is_monitor:
                print(f"{existing_student.name} 已经是班长")
                monitor_password = existing_student.student_id[-5:]
                print(f"班长管理密码: {monitor_password} (学号后5位)")
                return True
            
            # 询问是否要覆盖现有信息
            while True:
                choice = input(f"是否将 {existing_student.name} 设置为班长? (y/n): ")
                if choice.lower() in ['y', 'yes']:
                    # 将现有学生设置为班长
                    return set_as_monitor(existing_student)
                elif choice.lower() in ['n', 'no']:
                    print("操作已取消")
                    return False
                else:
                    print("无效输入，请输入 y 或 n")
        
        # 检查班级是否存在，不存在则创建
        class_obj = Class.query.filter_by(name=class_name).first()
        if not class_obj:
            print(f"班级 '{class_name}' 不存在，正在创建...")
            class_obj = Class(name=class_name)
            db.session.add(class_obj)
            try:
                db.session.commit()
                print(f"成功创建班级: {class_name}")
            except Exception as e:
                db.session.rollback()
                print(f"创建班级失败: {str(e)}")
                return False
        
        # 创建新学生
        new_student = User(
            name=name,
            student_id=student_id,
            class_id=class_obj.id,
            is_monitor=True
        )
        
        # 设置默认密码（学号）
        new_student.set_password(student_id)
        
        db.session.add(new_student)
        
        try:
            db.session.commit()
            monitor_password = new_student.student_id[-5:]
            print(f"成功: 已添加学生 {name} (学号: {student_id}) 到班级 {class_name} 并设置为班长")
            print(f"班长管理密码: {monitor_password} (学号后5位)")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"错误: 添加学生并设置班长失败 - {str(e)}")
            return False

def set_as_monitor(student):
    """将现有学生设置为班长
    
    Args:
        student: User对象
    
    Returns:
        bool: 操作是否成功
    """
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
    app = create_app()
    with app.app_context():
        print("交互式班长添加程序")
        print("输入格式: 班长姓名 学号 班级名称")
        print("可以一次输入多名班长，每行一个")
        print("输入 'q' 或 'exit' 退出程序")
        print("-" * 40)
        
        while True:
            user_input = input("\n请输入信息 (q 退出): ").strip()
            
            # 检查退出指令
            if user_input.lower() in ['q', 'exit', 'quit']:
                print("程序已退出")
                break
                
            # 解析输入
            try:
                parts = user_input.split()
                if len(parts) != 3:
                    print("错误: 输入格式不正确，请使用'姓名 学号 班级名称'格式")
                    continue
                    
                name, student_id, class_name = parts
                
                # 添加班长
                add_monitor(name, student_id, class_name)
                print("-" * 40)  # 分隔线
                
            except Exception as e:
                print(f"处理输入时出错: {str(e)}")