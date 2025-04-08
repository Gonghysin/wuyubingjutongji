from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"数据库中的用户数量: {len(users)}")
    
    if users:
        print("\n用户列表:")
        for user in users:
            print(f"ID: {user.id}, 学号: {user.student_id}, 姓名: {user.name}")
    else:
        print("\n数据库中没有用户数据。")
        print("请运行 python import_students.py 导入学生数据。")
