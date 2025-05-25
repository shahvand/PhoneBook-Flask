#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pymysql
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات دیتابیس MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'autocommit': True
}

def migrate_data():
    # اتصال به SQLite
    sqlite_path = os.path.join('data', 'database.db')
    if not os.path.exists(sqlite_path):
        sqlite_path = 'database.db'
    
    if not os.path.exists(sqlite_path):
        print("فایل دیتابیس SQLite پیدا نشد!")
        return
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    # اتصال به MySQL
    try:
        mysql_conn = pymysql.connect(**DB_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        
        print("شروع انتقال داده‌ها...")
        
        # انتقال جدول contacts
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM contacts")
        contacts = sqlite_cursor.fetchall()
        
        successful_contacts = 0
        for contact in contacts:
            try:
                # بررسی و تصحیح مقادیر NULL
                full_name = contact['full_name'] if contact['full_name'] else 'نامشخص'
                phone = contact['phone'] if contact['phone'] else ''
                position = contact['position'] if contact['position'] else ''
                department = contact['department'] if contact['department'] else ''
                location = contact['location'] if contact['location'] else ''
                
                # اگر شماره تلفن خالی است، از آن صرف نظر کنیم
                if not phone:
                    continue
                
                mysql_cursor.execute("""
                    INSERT INTO contacts (id, full_name, phone, position, department, location)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    full_name = VALUES(full_name),
                    position = VALUES(position),
                    department = VALUES(department),
                    location = VALUES(location)
                """, (contact['id'], full_name, phone, position, department, location))
                successful_contacts += 1
            except pymysql.Error as e:
                print(f"خطا در انتقال مخاطب {contact.get('full_name', 'نامشخص')}: {e}")
        
        # انتقال جدول logs
        sqlite_cursor.execute("SELECT * FROM logs")
        logs = sqlite_cursor.fetchall()
        
        successful_logs = 0
        for log in logs:
            try:
                mysql_cursor.execute("""
                    INSERT INTO logs (id, contact_id, action, ip_address, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    action = VALUES(action),
                    ip_address = VALUES(ip_address)
                """, (log['id'], log['contact_id'], log['action'], 
                     log['ip_address'], log['timestamp']))
                successful_logs += 1
            except pymysql.Error as e:
                print(f"خطا در انتقال لاگ {log['id']}: {e}")
        
        mysql_conn.commit()
        print(f"انتقال کامل شد! {successful_contacts} مخاطب و {successful_logs} لاگ با موفقیت منتقل شدند.")
        
    except pymysql.Error as e:
        print(f"خطا در اتصال به MySQL: {e}")
    finally:
        if 'mysql_conn' in locals():
            mysql_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data() 