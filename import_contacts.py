import pandas as pd
import sqlite3

# مسیر فایل Excel را مشخص کنید
excel_file = 'phone.xlsx'  # نام فایل Excel شما

# خواندن داده‌ها از فایل Excel بدون سرستون
df = pd.read_excel(excel_file, header=None)

# تنظیم نام ستون‌ها
df.columns = ['full_name', 'phone', 'position', 'department', 'location']

# ادامه اسکریپت به صورت قبل
# اطمینان از پر بودن فیلد phone
df = df[df['phone'].notna()]

# اتصال به دیتابیس
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# افزودن مخاطبین به جدول contacts
inserted_count = 0
for index, row in df.iterrows():
    cursor.execute('''
        INSERT INTO contacts (full_name, phone, position, department, location)
        VALUES (?, ?, ?, ?, ?)
    ''', (row['full_name'], str(row['phone']), row['position'], row['department'], row['location']))
    inserted_count += 1

conn.commit()
conn.close()

print(f'{inserted_count} مخاطب با موفقیت وارد شدند.')
