from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_wtf import CSRFProtect  # اضافه کردن این خط
import sqlite3
import bleach

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # حتماً یک کلید مخفی قوی جایگزین کنید

csrf = CSRFProtect(app)  # فعال کردن CSRF Protection

# تابع برای اتصال به دیتابیس
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
    return conn

# تابع برای دریافت متن اطلاعیه
def get_announcement_text():
    try:
        with open('announcement.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''  # در صورت عدم وجود فایل، متن خالی برمی‌گرداند

# تابع برای تنظیم متن اطلاعیه
def set_announcement_text(text):
    with open('announcement.txt', 'w', encoding='utf-8') as f:
        f.write(text)

# تابع برای بررسی مجوز ویرایش بر اساس آی‌پی کاربر
def user_can_edit():
    allowed_ips = ['192.168.202.12', '192.168.202.3']
    user_ip = request.remote_addr
    return user_ip in allowed_ips

# صفحه اصلی: نمایش لیست مخاطبین با مرتب‌سازی شماره تلفن از کم به زیاد
@app.route('/')
def index():
    conn = get_db_connection()
    contacts = conn.execute('SELECT * FROM contacts ORDER BY CAST(phone AS INTEGER) ASC').fetchall()
    conn.close()
    announcement_text = get_announcement_text()
    can_edit = user_can_edit()
    return render_template('index.html', contacts=contacts, announcement_text=announcement_text, user_can_edit=can_edit)

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

# مسیر برای به‌روزرسانی اطلاعیه
@app.route('/update-announcement', methods=['POST'])
def update_announcement():
    if not user_can_edit():
        return jsonify({'success': False}), 403
    data = request.get_json()
    new_text = data.get('announcement_text', '')

    # پاکسازی محتوای HTML
    allowed_tags = [
        'p', 'b', 'i', 'u', 'strong', 'em', 'a', 'img', 'ul', 'ol', 'li', 'br',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'table', 'tr', 'td', 'th'
    ]
    allowed_attributes = {
        '*': ['style', 'class'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
        'span': ['style', 'class'],
        'div': ['style', 'class'],
        'table': ['style', 'class', 'border'],
        'tr': ['style', 'class'],
        'td': ['style', 'class', 'colspan', 'rowspan'],
        'th': ['style', 'class', 'colspan', 'rowspan']
    }
    allowed_styles = ['text-align', 'color', 'background-color', 'font-size', 'height', 'width', 'border']

    cleaned_text = bleach.clean(
        new_text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        styles=allowed_styles,
        strip=True,
        strip_comments=True
    )

    set_announcement_text(cleaned_text)
    return jsonify({'success': True})

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
    app.run(debug=True)
