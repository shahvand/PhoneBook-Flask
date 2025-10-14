from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
from flask_wtf import CSRFProtect
import pymysql
import os
from dotenv import load_dotenv
import hashlib
import json
import socket
from datetime import datetime, timedelta
import gzip
import time

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_مهعامهعغهعلعنkey'  # حتماً یک کلید مخفی قوی جایگزین کنید

# فعال کردن CSRF Protection
csrf = CSRFProtect(app)

# کش ساده برای بهبود عملکرد
menu_cache = {
    'data': None,
    'last_update': 0
}

CACHE_TIMEOUT = 300  # 5 دقیقه

# تنظیمات دیتابیس MySQL بهینه شده از فایل .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 5,
    'read_timeout': 10,
    'write_timeout': 10
}

# تابع برای اتصال به دیتابیس MySQL بهینه شده
def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"خطا در اتصال به دیتابیس: {e}")
        return None

# تابع بهینه شده برای ثبت لاگ ویرایش
def log_edit_action(contact_id, contact_name, browser_name=''):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # دریافت آی‌پی کاربر
            user_ip = request.remote_addr or '127.0.0.1'
            forwarded_header = request.headers.get('X-Forwarded-For')
            if forwarded_header:
                user_ip = forwarded_header.split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                user_ip = request.headers.get('X-Real-IP')
            
            # دریافت نوع مرورگر از User-Agent
            user_agent = request.headers.get('User-Agent', '')
            if not browser_name:
                if 'Chrome' in user_agent and 'Edg' not in user_agent:
                    browser_name = 'Chrome'
                elif 'Firefox' in user_agent:
                    browser_name = 'Firefox'
                elif 'Edg' in user_agent:
                    browser_name = 'Edge'
                elif 'Safari' in user_agent and 'Chrome' not in user_agent:
                    browser_name = 'Safari'
                else:
                    browser_name = 'نامشخص'
            
            # ثبت لاگ ساده و واضح
            cursor.execute('''
                INSERT INTO logs (contact_id, action, ip_address, user_agent, computer_name, additional_info) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (contact_id, 'edit', user_ip, user_agent, browser_name, f'ویرایش مخاطب: {contact_name}'))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ لاگ ثبت شد: {contact_name} - آی‌پی: {user_ip} - مرورگر: {browser_name}")
        except pymysql.Error as e:
            print(f"❌ خطا در ثبت لاگ: {e}")

# تابع بهینه شده برای ثبت لاگ اضافه کردن مخاطب
def log_add_action(contact_id, contact_name, browser_name=''):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # دریافت آی‌پی کاربر
            user_ip = request.remote_addr or '127.0.0.1'
            forwarded_header = request.headers.get('X-Forwarded-For')
            if forwarded_header:
                user_ip = forwarded_header.split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                user_ip = request.headers.get('X-Real-IP')
            
            # دریافت نوع مرورگر از User-Agent
            user_agent = request.headers.get('User-Agent', '')
            if not browser_name:
                if 'Chrome' in user_agent and 'Edg' not in user_agent:
                    browser_name = 'Chrome'
                elif 'Firefox' in user_agent:
                    browser_name = 'Firefox'
                elif 'Edg' in user_agent:
                    browser_name = 'Edge'
                elif 'Safari' in user_agent and 'Chrome' not in user_agent:
                    browser_name = 'Safari'
                else:
                    browser_name = 'نامشخص'
            
            # ثبت لاگ اضافه کردن
            cursor.execute('''
                INSERT INTO logs (contact_id, action, ip_address, user_agent, computer_name, additional_info) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (contact_id, 'add', user_ip, user_agent, browser_name, f'اضافه کردن مخاطب جدید: {contact_name}'))
            
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ لاگ اضافه کردن ثبت شد: {contact_name} - آی‌پی: {user_ip} - مرورگر: {browser_name}")
        except pymysql.Error as e:
            print(f"❌ خطا در ثبت لاگ اضافه کردن: {e}")

# تابع ایجاد دیتابیس و جداول
def init_database():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # ایجاد جدول contacts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50) UNIQUE NOT NULL,
                    position VARCHAR(255),
                    department VARCHAR(255),
                    location VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    contact_id INT,
                    action VARCHAR(50),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    computer_name VARCHAR(255),
                    additional_info TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول admin_settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول menu_items
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    url VARCHAR(500) NOT NULL,
                    icon VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # اضافه کردن پسورد پیش‌فرض ادمین اگر وجود ندارد
            cursor.execute("SELECT COUNT(*) FROM admin_settings WHERE setting_key = 'admin_password'")
            result = cursor.fetchone()
            if result and result['COUNT(*)'] == 0:
                default_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute("INSERT INTO admin_settings (setting_key, setting_value) VALUES ('admin_password', %s)", (default_password,))
            
            # اضافه کردن تنظیم محدودیت آی‌پی (پیش‌فرض: فعال = 1, غیرفعال = 0)
            cursor.execute("SELECT COUNT(*) FROM admin_settings WHERE setting_key = 'ip_restriction_enabled'")
            result = cursor.fetchone()
            if result and result['COUNT(*)'] == 0:
                cursor.execute("INSERT INTO admin_settings (setting_key, setting_value) VALUES ('ip_restriction_enabled', '0')")
            
            # اضافه کردن آیتم‌های منوی پیش‌فرض
            cursor.execute("SELECT COUNT(*) FROM menu_items")
            result = cursor.fetchone()
            if result and result['COUNT(*)'] == 0:
                default_menu_items = [
                    ('حضور و غیاب', '#', 'clock', 1, 1),
                    ('اتوماسیون اداری', '#', 'briefcase', 1, 2),
                    ('ایمیل تحت وب', '#', 'mail', 1, 3),
                    ('هلپ', '#', 'help-circle', 1, 4),
                    ('اخبار', '#', 'file-text', 1, 5),
                    ('فایل شیرینگ', '#', 'share-2', 1, 6)
                ]
                for item in default_menu_items:
                    cursor.execute("INSERT INTO menu_items (title, url, icon, is_active, sort_order) VALUES (%s, %s, %s, %s, %s)", item)
            
            conn.commit()
            cursor.close()
            print("جداول با موفقیت ایجاد شدند.")
        except pymysql.Error as e:
            print(f"خطا در ایجاد جداول: {e}")
        finally:
            conn.close()

# اجرای تابع ایجاد دیتابیس در ابتدای برنامه
init_database()

# تابع برای بررسی مجوز ویرایش - همه کاربران مجاز هستند
def user_can_edit():
    # همه کاربران می‌توانند مخاطب اضافه کنند و ویرایش کنند
    return True
    
    # بررسی متغیر محیطی برای غیرفعال کردن محدودیت آی‌پی
    disable_ip_restriction = os.getenv('DISABLE_IP_RESTRICTION', 'false').lower() == 'true'
    if disable_ip_restriction:
        return True
    
    # بررسی تنظیمات ادمین برای فعال/غیرفعال بودن محدودیت آی‌پی
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'ip_restriction_enabled'")
            ip_restriction_result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            # اگر محدودیت آی‌پی غیرفعال باشد، همه کاربران می‌توانند ویرایش کنند
            if ip_restriction_result and ip_restriction_result['setting_value'] == '0':
                return True
                
        except pymysql.Error as e:
            print(f"خطا در بررسی تنظیمات آی‌پی: {e}")
    
    # آی‌پی‌های مجاز شامل محیط Docker
    allowed_ips = [
        '192.168.202.12', 
        '192.168.202.3',
        '127.0.0.1',
        '192.168.100.26',  # آی‌پی هاست Docker
        '172.21.0.3',      # آی‌پی داخلی Docker
        '::1'              # IPv6 localhost
    ]
    user_ip = request.remote_addr or '127.0.0.1'
    
    # بررسی آی‌پی‌های شبکه Docker (172.x.x.x)
    if user_ip and (user_ip.startswith('172.') or user_ip.startswith('192.168.')):
        return True
    
    return user_ip in allowed_ips

# تابع بهینه شده برای دریافت آیتم‌های منو با کش
def get_menu_items():
    current_time = time.time()
    
    # بررسی کش
    if (menu_cache['data'] is not None and 
        current_time - menu_cache['last_update'] < CACHE_TIMEOUT):
        return menu_cache['data']
    
    # بروزرسانی کش
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('SELECT * FROM menu_items WHERE is_active = 1 ORDER BY sort_order')
            menu_items = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # ذخیره در کش
            menu_cache['data'] = menu_items
            menu_cache['last_update'] = current_time
            
            return menu_items
        except pymysql.Error as e:
            print(f"خطا در خواندن منو: {e}")
            return menu_cache['data'] if menu_cache['data'] else []
    return menu_cache['data'] if menu_cache['data'] else []

# تابع برای بررسی احراز هویت ادمین
def check_admin_auth():
    return session.get('admin_logged_in', False)

# تابع برای اضافه کردن cache headers
@app.after_request
def add_cache_headers(response):
    # اضافه کردن cache headers
    if request.endpoint == 'static':
        # برای فایل‌های استاتیک کش یک روزه
        response.cache_control.max_age = 86400  # 1 روز
        response.cache_control.public = True
    elif request.endpoint == 'index':
        # برای صفحه اصلی کش 5 دقیقه‌ای
        response.cache_control.max_age = 300  # 5 دقیقه
        response.cache_control.public = True
    
    return response

# صفحه اصلی بهینه شده: نمایش لیست مخاطبین
@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "خطا در اتصال به دیتابیس", 500
    
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        # بهینه‌سازی کوئری: فقط فیلدهای مورد نیاز را انتخاب کنیم
        cursor.execute('''
            SELECT id, full_name, phone, position, department, location 
            FROM contacts 
            ORDER BY CAST(phone AS UNSIGNED) ASC
        ''')
        contacts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # محاسبه can_edit یکبار (همه کاربران مجاز هستند)
        can_edit = user_can_edit()
        
        # دریافت منو از کش
        menu_items = get_menu_items()
        
        return render_template('index.html', contacts=contacts, user_can_edit=can_edit, menu_items=menu_items)
    except pymysql.Error as e:
        print(f"خطا در خواندن داده‌ها: {e}")
        return "خطا در خواندن داده‌ها", 500

# API بهینه شده برای دریافت سریع مخاطبین (JSON)
@app.route('/api/contacts')
def api_contacts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطا در اتصال به دیتابیس'}), 500
    
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('''
            SELECT id, full_name, phone, position, department, location 
            FROM contacts 
            ORDER BY CAST(phone AS UNSIGNED) ASC
        ''')
        contacts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'contacts': contacts, 'count': len(contacts)})
    except pymysql.Error as e:
        print(f"خطا در خواندن داده‌ها: {e}")
        return jsonify({'error': 'خطا در خواندن داده‌ها'}), 500

# تست endpoint برای دیباگ مشکل دکمه اضافه کردن
@app.route('/debug/permissions')
def debug_permissions():
    user_ip = request.remote_addr or '127.0.0.1'
    can_edit = user_can_edit()
    disable_ip_restriction = os.getenv('DISABLE_IP_RESTRICTION', 'false').lower()
    
    # بررسی تنظیمات دیتابیس
    db_setting = None
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'ip_restriction_enabled'")
            result = cursor.fetchone()
            if result:
                db_setting = result['setting_value']
            cursor.close()
            conn.close()
        except:
            pass
    
    debug_info = {
        'user_ip': user_ip,
        'can_edit': can_edit,
        'env_disable_ip_restriction': disable_ip_restriction,
        'db_ip_restriction_enabled': db_setting,
        'headers': dict(request.headers),
        'remote_addr': request.remote_addr,
        'forwarded_for': request.headers.get('X-Forwarded-For'),
        'real_ip': request.headers.get('X-Real-IP')
    }
    
    return jsonify(debug_info)

# ورود ادمین
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'admin_password'")
                    stored_password = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if stored_password and stored_password['setting_value'] == hashed_password:
                        session['admin_logged_in'] = True
                        flash('با موفقیت وارد شدید', 'success')
                        return redirect(url_for('admin_settings'))
                    else:
                        flash('پسورد اشتباه است', 'error')
                except pymysql.Error as e:
                    flash('خطا در بررسی پسورد', 'error')
        else:
            flash('لطفاً پسورد را وارد کنید', 'error')
    
    return render_template('admin_login.html')

# خروج ادمین
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('با موفقیت خارج شدید', 'success')
    return redirect(url_for('index'))

# صفحه تنظیمات ادمین
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'change_password':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password and new_password == confirm_password:
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE admin_settings SET setting_value = %s WHERE setting_key = 'admin_password'", (hashed_password,))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        flash('پسورد با موفقیت تغییر کرد', 'success')
                    except pymysql.Error as e:
                        flash('خطا در تغییر پسورد', 'error')
            else:
                flash('پسوردها مطابقت ندارند', 'error')
        
        elif action == 'toggle_ip_restriction':
            ip_restriction = '1' if request.form.get('ip_restriction') else '0'
            
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE admin_settings SET setting_value = %s WHERE setting_key = 'ip_restriction_enabled'", (ip_restriction,))
                    if cursor.rowcount == 0:
                        cursor.execute("INSERT INTO admin_settings (setting_key, setting_value) VALUES ('ip_restriction_enabled', %s)", (ip_restriction,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    status = 'فعال' if ip_restriction == '1' else 'غیرفعال'
                    flash(f'محدودیت آی‌پی {status} شد', 'success')
                except pymysql.Error as e:
                    flash('خطا در تغییر تنظیمات', 'error')
    
    # دریافت آیتم‌های منو و تنظیمات برای نمایش
    conn = get_db_connection()
    menu_items = []
    ip_restriction_enabled = True  # پیش‌فرض فعال
    
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('SELECT * FROM menu_items ORDER BY sort_order')
            menu_items = cursor.fetchall()
            
            # دریافت تنظیم محدودیت آی‌پی
            cursor.execute("SELECT setting_value FROM admin_settings WHERE setting_key = 'ip_restriction_enabled'")
            ip_restriction_result = cursor.fetchone()
            if ip_restriction_result:
                ip_restriction_enabled = ip_restriction_result['setting_value'] == '1'
            
            cursor.close()
            conn.close()
        except pymysql.Error as e:
            print(f"خطا در خواندن تنظیمات: {e}")
    
    return render_template('admin_settings.html', menu_items=menu_items, ip_restriction_enabled=ip_restriction_enabled)

# ویرایش مخاطب
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    if not conn:
        return "خطا در اتصال به دیتابیس", 500
    
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM contacts WHERE id = %s', (id,))
        contact = cursor.fetchone()

        if request.method == 'POST' and contact:
            full_name = request.form['full_name']
            phone = contact['phone']  # شماره تلفن از دیتابیس گرفته می‌شود و نمی‌توان آن را تغییر داد
            position = request.form.get('position')
            department = request.form.get('department')
            location = request.form.get('location')
            browser_name = request.form.get('computer_name', '')  # حالا نام مرورگر است

            if not phone:
                return "فیلد شماره تلفن نمی‌تواند خالی باشد.", 400

            cursor.execute('''
                UPDATE contacts 
                SET full_name = %s, position = %s, department = %s, location = %s
                WHERE id = %s
            ''', (full_name, position, department, location, id))

            # ثبت لاگ ساده
            log_edit_action(id, full_name, browser_name)
            
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('index'))

        cursor.close()
        conn.close()
        return render_template('edit.html', contact=contact)
    except pymysql.Error as e:
        print(f"خطا در ویرایش مخاطب: {e}")
        return "خطا در ویرایش مخاطب", 500

# افزودن مخاطب جدید - همه کاربران مجاز هستند
@app.route('/add', methods=('GET', 'POST'))
def add():
    # همه کاربران می‌توانند مخاطب جدید اضافه کنند
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        position = request.form.get('position', '')
        department = request.form.get('department', '')
        location = request.form.get('location', '')
        
        # بررسی اینکه فیلدهای ضروری پر شده باشند
        if not full_name or not phone:
            flash('نام کامل و شماره تلفن الزامی است.', 'error')
            return render_template('add.html')
        
        # بررسی تکراری نبودن شماره تلفن
        conn = get_db_connection()
        if not conn:
            flash('خطا در اتصال به دیتابیس', 'error')
            return render_template('add.html')
        
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM contacts WHERE phone = %s', (phone,))
            result = cursor.fetchone()
            if result and result['COUNT(*)'] > 0:
                flash('این شماره تلفن قبلاً ثبت شده است.', 'error')
                cursor.close()
                conn.close()
                return render_template('add.html')
            
            # اضافه کردن مخاطب جدید
            cursor.execute('''
                INSERT INTO contacts (full_name, phone, position, department, location)
                VALUES (%s, %s, %s, %s, %s)
            ''', (full_name, phone, position, department, location))
            
            # دریافت ID مخاطب جدید
            new_contact_id = cursor.lastrowid
            
            # ثبت لاگ اضافه کردن
            log_add_action(new_contact_id, full_name)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash(f'مخاطب "{full_name}" با موفقیت اضافه شد.', 'success')
            return redirect(url_for('index'))
            
        except pymysql.Error as e:
            print(f"خطا در اضافه کردن مخاطب: {e}")
            flash('خطا در اضافه کردن مخاطب. لطفاً دوباره تلاش کنید.', 'error')
            if cursor:
                cursor.close()
            conn.close()
            return render_template('add.html')
    
    return render_template('add.html')

# نمایش لاگ‌ها - فقط برای ادمین
@app.route('/admin/logs')
def view_logs():
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if not conn:
        return "خطا در اتصال به دیتابیس", 500
    
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('''
            SELECT logs.*, contacts.full_name
            FROM logs
            LEFT JOIN contacts ON logs.contact_id = contacts.id
            WHERE logs.action IN ('edit', 'add')
            ORDER BY logs.timestamp DESC
            LIMIT 100
        ''')
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # محاسبه آمار - ویرایش‌ها و اضافه کردن‌ها
        total_logs = len(logs)
        edit_count = sum(1 for log in logs if log['action'] == 'edit')
        add_count = sum(1 for log in logs if log['action'] == 'add')
        unique_computers = len(set(log['computer_name'] for log in logs if log['computer_name']))
        
        stats = {
            'total_logs': total_logs,
            'edit_count': edit_count,
            'add_count': add_count,
            'unique_computers': unique_computers
        }
        
        return render_template('logs.html', logs=logs, stats=stats)
    except pymysql.Error as e:
        print(f"خطا در خواندن لاگ‌ها: {e}")
        return "خطا در خواندن لاگ‌ها", 500

if __name__ == '__main__':
    # تنظیمات برای محیط تولید
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # بهینه‌سازی برای production
    if not debug_mode:
        # حذف warning های غیرضروری
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)