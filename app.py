from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_wtf import CSRFProtect
import sqlite3
import bleach
import json
from bleach.css_sanitizer import CSSSanitizer

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # حتماً یک کلید مخفی قوی جایگزین کنید

csrf = CSRFProtect(app)  # فعال کردن CSRF Protection

# تابع برای اتصال به دیتابیس
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
    return conn

# تابع برای دریافت داده‌های اطلاعیه
def get_announcement_data():
    try:
        with open('announcement.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
            return {'text': '', 'hidden': False}  # مقدار پیش‌فرض

# تابع برای تنظیم داده‌های اطلاعیه
def set_announcement_data(data):
    with open('announcement.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    announcement_data = get_announcement_data()
    can_edit = user_can_edit()
    return render_template('index.html', contacts=contacts, announcement_data=announcement_data, user_can_edit=can_edit)

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
    hidden = data.get('hidden', False)

    # پاکسازی محتوای HTML
    allowed_tags = [
        'p', 'b', 'i', 'u', 'strong', 'em', 'a', 'img', 'ul', 'ol', 'li', 'br',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'table', 'tr', 'td', 'th', 'blockquote'
    ]
    allowed_attributes = {
        '*': ['style', 'class', 'align', 'dir'],
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

    # ایجاد نمونه‌ای از CSSSanitizer
    css_sanitizer = CSSSanitizer(allowed_css_properties=allowed_styles)

    # پاکسازی متن ورودی
    cleaned_text = bleach.clean(
        new_text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        css_sanitizer=css_sanitizer,
        strip=True,
        strip_comments=True
    )

    # ذخیره متن و وضعیت مخفی بودن
    announcement_data = {'text': cleaned_text, 'hidden': hidden}
    set_announcement_data(announcement_data)
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
