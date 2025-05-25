# استفاده از تصویر پایه پایتون ۳.۱۱ نسخه سبک (slim)
FROM python:3.11-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تنظیم دایرکتوری کاری در داخل کانتینر
WORKDIR /app

# کپی فایل‌های requirements
COPY requirements.txt .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد برنامه
COPY . .

# ایجاد دایرکتوری static اگر وجود نداشته باشد
RUN mkdir -p static

# تنظیم مجوزها
RUN chmod +x app.py

# باز کردن پورت ۵۰۰۰ برای برنامه Flask
EXPOSE 5000

# فرمان اجرا برای شروع برنامه
CMD ["python", "app.py"]
