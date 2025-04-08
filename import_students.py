import pandas as pd
from app import create_app
from app.models import db, User

def import_students():
    app = create_app()
    
    with app.app_context():
        # 读取Excel文件
        df = pd.read_excel('光实2401名单 最新.xlsx')
        
        # 遍历每一行数据
        for _, row in df.iterrows():
            # 假设Excel中的列名为"姓名"和"学号"
            # 如果列名不同，请相应修改
            name = row['姓名']
            student_id = str(row['学号'])
            
            # 检查学生是否已存在
            existing_student = User.query.filter_by(student_id=student_id).first()
            
            if not existing_student:
                # 创建新学生记录
                student = User(
                    name=name,
                    student_id=student_id
                )
                # 设置密码为学号后5位
                password = student_id[-5:] if len(student_id) >= 5 else student_id
                student.set_password(password)
                
                db.session.add(student)
                print(f"添加学生: {name} ({student_id})")
            else:
                print(f"学生已存在: {name} ({student_id})")
        
        # 提交所有更改
        try:
            db.session.commit()
            print("所有学生数据导入成功！")
        except Exception as e:
            db.session.rollback()
            print(f"导入过程中出现错误: {str(e)}")

if __name__ == '__main__':
    import_students() 