from app import create_app, db
from app.models import User
import pandas as pd

def import_students():
    app = create_app()
    with app.app_context():
        # 读取Excel文件
        df = pd.read_excel('光实2401名单 最新.xlsx')
        
        # 遍历每一行数据
        for _, row in df.iterrows():
            # 创建用户对象
            user = User(
                student_id=str(row['学号']),  # 确保学号是字符串
                name=row['姓名']
            )
            # 设置默认密码为学号
            user.set_password(str(row['学号']))
            
            # 检查用户是否已存在
            existing_user = User.query.filter_by(student_id=user.student_id).first()
            if existing_user:
                print(f"用户 {user.name} ({user.student_id}) 已存在，跳过")
                continue
            
            # 添加到数据库
            db.session.add(user)
            print(f"添加用户: {user.name} ({user.student_id})")
        
        # 提交更改
        try:
            db.session.commit()
            print("所有用户导入成功！")
        except Exception as e:
            db.session.rollback()
            print(f"导入失败: {str(e)}")

if __name__ == '__main__':
    import_students() 