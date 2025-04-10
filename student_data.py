import pandas as pd

# 创建一个包含单个学生信息的DataFrame
data = {
    '学号': ['U202414049'],
    '姓名': ['龚海心']
}

df = pd.DataFrame(data)

# 保存为Excel文件
df.to_excel('student_data.xlsx', index=False)
print("已创建学生数据Excel文件: student_data.xlsx")