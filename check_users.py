from app import create_app
from app.models import User, Class

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f"数据库中的用户数量: {len(users)}")
    
    if users:
        print("\n用户列表:")
        for user in users:
            class_name = user.class_.name if user.class_ else "无班级"
            monitor_status = "是" if user.is_monitor else "否"
            print(f"ID: {user.id}, 学号: {user.student_id}, 姓名: {user.name}, 班级: {class_name}, 班长: {monitor_status}")
    else:
        print("\n数据库中没有用户数据。")
        print("请运行 python import_students.py 导入学生数据。")

