from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import CSRFProtect
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # حتماً یک کلید مخفی قوی جایگزین کنید

csrf = CSRFProtect(app)  # فعال کردن CSRF Protection
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# اطمینان از وجود پوشه data
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# تابع برای اتصال به دیتابیس
def get_db_connection():
    db_path = os.path.join(DATA_DIR, 'database.db')
    
    # اگر دیتابیس وجود ندارد، آن را ایجاد کنید
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                position TEXT,
                department TEXT,
                location TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                action TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        conn.commit()
        conn.close()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# تابع برای بررسی مجوز ویرایش بر اساس آی‌پی کاربر
def user_can_edit():
    allowed_ips = ['192.168.202.12', '192.168.202.3','127.0.0.1']
    user_ip = request.remote_addr
    return user_ip in allowed_ips

# صفحه اصلی: نمایش لیست مخاطبین با مرتب‌سازی شماره تلفن از کم به زیاد
@app.route('/')
def index():
    conn = get_db_connection()
    contacts = conn.execute('SELECT * FROM contacts ORDER BY CAST(phone AS INTEGER) ASC').fetchall()
    conn.close()
    can_edit = user_can_edit()
    return render_template('index.html', contacts=contacts, user_can_edit=can_edit)

# ویرایش مخاطب
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    contact = conn.execute('SELECT * FROM contacts WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = contact['phone']  # شماره تلفن از دیتابیس گرفته می‌شود و نمی‌توان آن را تغییر داد
        position = request.form.get('position')
        department = request.form.get('department')
        location = request.form.get('location')

        if not phone:
            return "فیلد شماره تلفن نمی‌تواند خالی باشد.", 400

        conn.execute('''
            UPDATE contacts 
            SET full_name = ?, position = ?, department = ?, location = ?
            WHERE id = ?
        ''', (full_name, position, department, location, id))
        conn.commit()

        # ثبت لاگ
        ip_address = request.remote_addr
        conn.execute('INSERT INTO logs (contact_id, action, ip_address) VALUES (?, ?, ?)',
                     (id, 'edit', ip_address))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', contact=contact)

# نمایش لاگ‌ها
@app.route('/logs')
def view_logs():
    conn = get_db_connection()
    logs = conn.execute('''
        SELECT logs.*, contacts.full_name
        FROM logs
        LEFT JOIN contacts ON logs.contact_id = contacts.id
        ORDER BY logs.timestamp DESC
    ''').fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

# مسیر افزودن مخاطب غیرفعال شده است
@app.route('/add', methods=('GET', 'POST'))
def add():
    return "افزودن مخاطب جدید غیرفعال است.", 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
