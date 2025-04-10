from app import create_app, db
from app.models import User, Class
import pandas as pd
import os

def import_students(file_path, class_id=None, class_name=None):
    """导入学生名单
    
    Args:
        file_path: Excel文件路径
        class_id: 班级ID，如果提供则将学生添加到该班级
        class_name: 班级名称，如果提供且class_id为None，则创建新班级
    """
    app = create_app()
    with app.app_context():
        # 处理班级
        target_class = None
        if class_id:
            target_class = Class.query.get(class_id)
            if not target_class:
                print(f"班级ID {class_id} 不存在")
                return False
        elif class_name:
            # 检查班级是否已存在
            existing_class = Class.query.filter_by(name=class_name).first()
            if existing_class:
                target_class = existing_class
                print(f"使用已存在的班级: {class_name}")
            else:
                # 创建新班级
                target_class = Class(name=class_name)
                db.session.add(target_class)
                db.session.flush()  # 获取新创建班级的ID
                print(f"创建新班级: {class_name}")
        
        # 读取Excel文件
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在")
            return False
            
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            return False
        
        # 检查必要的列是否存在
        required_columns = ['学号', '姓名']
        for col in required_columns:
            if col not in df.columns:
                print(f"Excel文件缺少必要的列: {col}")
                return False
        
        # 遍历每一行数据
        added_count = 0
        skipped_count = 0
        for _, row in df.iterrows():
            # 创建用户对象
            user = User(
                student_id=str(row['学号']),  # 确保学号是字符串
                name=row['姓名']
            )
            # 设置默认密码为学号
            user.set_password(str(row['学号']))
            
            # 关联到班级
            if target_class:
                user.class_id = target_class.id
            
            # 检查用户是否已存在
            existing_user = User.query.filter_by(student_id=user.student_id).first()
            if existing_user:
                print(f"用户 {user.name} ({user.student_id}) 已存在，跳过")
                skipped_count += 1
                continue
            
            # 添加到数据库
            db.session.add(user)
            print(f"添加用户: {user.name} ({user.student_id})")
            added_count += 1
        
        # 提交更改
        try:
            db.session.commit()
            print(f"导入完成: 添加 {added_count} 名学生, 跳过 {skipped_count} 名已存在学生")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"导入失败: {str(e)}")
            return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='导入学生名单')
    parser.add_argument('--file', '-f', required=True, help='Excel文件路径')
    parser.add_argument('--class-name', '-c', help='班级名称，如果不存在则创建')
    parser.add_argument('--class-id', '-i', type=int, help='班级ID，如果提供则使用已存在的班级')
    
    args = parser.parse_args()
    
    import_students(args.file, args.class_id, args.class_name)