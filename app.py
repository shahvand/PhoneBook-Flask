from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# تابع برای اتصال به دیتابیس
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # برای دسترسی به ستون‌ها با نام
    return conn

# صفحه اصلی: نمایش لیست مخاطبین با مرتب‌سازی شماره تلفن از کم به زیاد
@app.route('/')
def index():
    conn = get_db_connection()
    contacts = conn.execute('SELECT * FROM contacts ORDER BY CAST(phone AS INTEGER) ASC').fetchall()
    conn.close()
    return render_template('index.html', contacts=contacts)

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
    app.run(debug=True)
