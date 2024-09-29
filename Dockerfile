# استفاده از تصویر پایه پایتون ۳.۹ نسخه سبک (slim)
FROM python:3.9-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تنظیم دایرکتوری کاری در داخل کانتینر
WORKDIR /app

# کپی کردن فایل‌های مورد نیاز
COPY requirements.txt /app/

# به‌روزرسانی pip و نصب وابستگی‌ها
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# کپی کردن کدهای برنامه به داخل کانتینر
COPY . /app/

# باز کردن پورت ۵۰۰۰ برای برنامه Flask
EXPOSE 5000

# فرمان اجرا برای شروع برنامه
CMD ["python", "app.py"]
