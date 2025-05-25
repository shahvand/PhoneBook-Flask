#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

def create_database():
    # تنظیمات اتصال بدون نام دیتابیس
    connection_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'charset': 'utf8mb4'
    }
    
    database_name = os.getenv('DB_NAME')
    
    try:
        # اتصال به MySQL بدون انتخاب دیتابیس
        conn = pymysql.connect(**connection_config)
        cursor = conn.cursor()
        
        # ایجاد دیتابیس
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"دیتابیس '{database_name}' با موفقیت ایجاد شد.")
        
        # انتخاب دیتابیس
        cursor.execute(f"USE `{database_name}`")
        
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
        
        # ایجاد جدول logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contact_id INT,
                action VARCHAR(50),
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        conn.commit()
        print("جداول با موفقیت ایجاد شدند.")
        
    except pymysql.Error as e:
        print(f"خطا در ایجاد دیتابیس: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_database() 