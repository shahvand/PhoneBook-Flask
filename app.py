from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import CSRFProtect
import pymysql
import os
from dotenv import load_dotenv
import hashlib
import json
import socket

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_مهعامهعغهعلعنkey'  # حتماً یک کلید مخفی قوی جایگزین کنید

# فعال کردن CSRF Protection
csrf = CSRFProtect(app)

# تنظیمات دیتابیس MySQL از فایل .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# تابع برای اتصال به دیتابیس MySQL
def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.Error as e:
        print(f"خطا در اتصال به دیتابیس: {e}")
        return None

# تابع برای دریافت اطلاعات کاربر
def get_user_info():
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # دریافت نام کامپیوتر واقعی
    computer_name = ''
    try:
        # استفاده از socket برای دریافت نام کامپیوتر سرور
        computer_name = socket.gethostname()
        
        # اگر نام کامپیوتر خالی بود، سعی کن از متغیرهای محیطی استفاده کنی
        if not computer_name:
            computer_name = os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'نامشخص'))
    except:
        computer_name = 'نامشخص'
    
    return {
        'ip_address': user_ip,
        'user_agent': user_agent,
        'computer_name': computer_name
    }

# تابع برای ثبت لاگ با اطلاعات کامل - فقط برای ویرایش
def log_action(contact_id, action, additional_info=''):
    # فقط لاگ ویرایش ثبت می‌شود
    if action != 'edit':
        return
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            user_info = get_user_info()
            
            # ثبت لاگ با اطلاعات کامل
            cursor.execute('''
                INSERT INTO logs (contact_id, action, ip_address, user_agent, computer_name, additional_info) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (contact_id, action, user_info['ip_address'], user_info['user_agent'], 
                  user_info['computer_name'], additional_info))
            
            conn.commit()
            cursor.close()
            conn.close()
        except pymysql.Error as e:
            print(f"خطا در ثبت لاگ: {e}")

# تابع برای ایجاد جداول در صورت عدم وجود
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
                    location VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # ایجاد جدول logs با ستون‌های جدید
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
            
            # بررسی و اضافه کردن ستون‌های جدید اگر وجود ندارند
            try:
                cursor.execute("ALTER TABLE logs ADD COLUMN user_agent TEXT")
            except:
                pass  # ستون از قبل موجود است
            
            try:
                cursor.execute("ALTER TABLE logs ADD COLUMN computer_name VARCHAR(255)")
            except:
                pass  # ستون از قبل موجود است
                
            try:
                cursor.execute("ALTER TABLE logs ADD COLUMN additional_info TEXT")
            except:
                pass  # ستون از قبل موجود است
            
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
            if cursor.fetchone()[0] == 0:
                default_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute("INSERT INTO admin_settings (setting_key, setting_value) VALUES ('admin_password', %s)", (default_password,))
            
            # اضافه کردن آیتم‌های منوی پیش‌فرض
            cursor.execute("SELECT COUNT(*) FROM menu_items")
            if cursor.fetchone()[0] == 0:
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

# تابع برای بررسی مجوز ویرایش بر اساس آی‌پی کاربر
def user_can_edit():
    allowed_ips = ['192.168.202.12', '192.168.202.3','127.0.0.1']
    user_ip = request.remote_addr
    return user_ip in allowed_ips

# تابع برای دریافت آیتم‌های منو
def get_menu_items():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('SELECT * FROM menu_items WHERE is_active = 1 ORDER BY sort_order')
            menu_items = cursor.fetchall()
            cursor.close()
            conn.close()
            return menu_items
        except pymysql.Error as e:
            print(f"خطا در خواندن منو: {e}")
            return []
    return []

# تابع برای بررسی احراز هویت ادمین
def check_admin_auth():
    return session.get('admin_logged_in', False)

# صفحه اصلی: نمایش لیست مخاطبین با مرتب‌سازی شماره تلفن از کم به زیاد
@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        return "خطا در اتصال به دیتابیس", 500
    
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT * FROM contacts ORDER BY CAST(phone AS UNSIGNED) ASC')
        contacts = cursor.fetchall()
        cursor.close()
        conn.close()
        can_edit = user_can_edit()
        menu_items = get_menu_items()
        
        # ثبت لاگ بازدید از صفحه اصلی
        log_action(None, 'page_visit', 'صفحه اصلی')
        
        return render_template('index.html', contacts=contacts, user_can_edit=can_edit, menu_items=menu_items)
    except pymysql.Error as e:
        print(f"خطا در خواندن داده‌ها: {e}")
        return "خطا در خواندن داده‌ها", 500

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
                    
                    if stored_password and stored_password[0] == hashed_password:
                        session['admin_logged_in'] = True
                        log_action(None, 'admin_login', 'ورود موفق به پنل ادمین')
                        flash('با موفقیت وارد شدید', 'success')
                        return redirect(url_for('admin_settings'))
                    else:
                        log_action(None, 'admin_login_failed', 'تلاش ناموفق برای ورود به پنل ادمین')
                        flash('پسورد اشتباه است', 'error')
                except pymysql.Error as e:
                    flash('خطا در بررسی پسورد', 'error')
        else:
            flash('لطفاً پسورد را وارد کنید', 'error')
    
    return render_template('admin_login.html')

# خروج ادمین
@app.route('/admin/logout')
def admin_logout():
    log_action(None, 'admin_logout', 'خروج از پنل ادمین')
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
                        log_action(None, 'password_change', 'تغییر پسورد ادمین')
                        flash('پسورد با موفقیت تغییر کرد', 'success')
                    except pymysql.Error as e:
                        flash('خطا در تغییر پسورد', 'error')
            else:
                flash('پسوردها مطابقت ندارند', 'error')
    
    # دریافت آیتم‌های منو برای نمایش
    conn = get_db_connection()
    menu_items = []
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('SELECT * FROM menu_items ORDER BY sort_order')
            menu_items = cursor.fetchall()
            cursor.close()
            conn.close()
        except pymysql.Error as e:
            print(f"خطا در خواندن منو: {e}")
    
    return render_template('admin_settings.html', menu_items=menu_items)

# مدیریت آیتم‌های منو
@app.route('/admin/menu', methods=['POST'])
def admin_menu():
    if not check_admin_auth():
        return redirect(url_for('admin_login'))
    
    action = request.form.get('action')
    conn = get_db_connection()
    
    if not conn:
        flash('خطا در اتصال به دیتابیس', 'error')
        return redirect(url_for('admin_settings'))
    
    try:
        cursor = conn.cursor()
        
        if action == 'add':
            title = request.form.get('title')
            url = request.form.get('url')
            icon = request.form.get('icon')
            
            if title and url:
                cursor.execute("INSERT INTO menu_items (title, url, icon, is_active, sort_order) VALUES (%s, %s, %s, 1, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM menu_items m))", (title, url, icon))
                log_action(None, 'menu_add', f'افزودن آیتم منو: {title}')
                flash('آیتم منو اضافه شد', 'success')
            else:
                flash('عنوان و لینک الزامی است', 'error')
        
        elif action == 'edit':
            item_id = request.form.get('item_id')
            title = request.form.get('title')
            url = request.form.get('url')
            icon = request.form.get('icon')
            is_active = 1 if request.form.get('is_active') else 0
            
            if item_id and title and url:
                cursor.execute("UPDATE menu_items SET title = %s, url = %s, icon = %s, is_active = %s WHERE id = %s", (title, url, icon, is_active, item_id))
                log_action(None, 'menu_edit', f'ویرایش آیتم منو: {title}')
                flash('آیتم منو ویرایش شد', 'success')
            else:
                flash('اطلاعات کامل نیست', 'error')
        
        elif action == 'delete':
            item_id = request.form.get('item_id')
            if item_id:
                # دریافت نام آیتم قبل از حذف
                cursor.execute("SELECT title FROM menu_items WHERE id = %s", (item_id,))
                item_title = cursor.fetchone()
                cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
                log_action(None, 'menu_delete', f'حذف آیتم منو: {item_title[0] if item_title else "نامشخص"}')
                flash('آیتم منو حذف شد', 'success')
        
        elif action == 'reorder':
            item_ids = request.form.getlist('item_order[]')
            for index, item_id in enumerate(item_ids):
                cursor.execute("UPDATE menu_items SET sort_order = %s WHERE id = %s", (index + 1, item_id))
            log_action(None, 'menu_reorder', 'تغییر ترتیب آیتم‌های منو')
            flash('ترتیب منو تغییر کرد', 'success')
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        flash('خطا در عملیات', 'error')
        print(f"خطا در مدیریت منو: {e}")
    
    return redirect(url_for('admin_settings'))

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

        if request.method == 'POST':
            full_name = request.form['full_name']
            phone = contact['phone']  # شماره تلفن از دیتابیس گرفته می‌شود و نمی‌توان آن را تغییر داد
            position = request.form.get('position')
            department = request.form.get('department')
            location = request.form.get('location')

            if not phone:
                return "فیلد شماره تلفن نمی‌تواند خالی باشد.", 400

            cursor.execute('''
                UPDATE contacts 
                SET full_name = %s, position = %s, department = %s, location = %s
                WHERE id = %s
            ''', (full_name, position, department, location, id))

            # ثبت لاگ با اطلاعات کامل
            log_action(id, 'edit', f'ویرایش مخاطب: {full_name}')
            
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
            WHERE logs.action = 'edit'
            ORDER BY logs.timestamp DESC
            LIMIT 100
        ''')
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # محاسبه آمار - فقط ویرایش‌ها
        total_logs = len(logs)
        unique_computers = len(set(log['computer_name'] for log in logs if log['computer_name']))
        
        stats = {
            'total_logs': total_logs,
            'edit_count': total_logs,  # همه لاگ‌ها ویرایش هستند
            'unique_computers': unique_computers
        }
        
        return render_template('logs.html', logs=logs, stats=stats)
    except pymysql.Error as e:
        print(f"خطا در خواندن لاگ‌ها: {e}")
        return "خطا در خواندن لاگ‌ها", 500

# مسیر افزودن مخاطب غیرفعال شده است
@app.route('/add', methods=('GET', 'POST'))
def add():
    return "افزودن مخاطب جدید غیرفعال است.", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
