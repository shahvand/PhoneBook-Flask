import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql', 'r', encoding='utf-8') as f:
    connection.executescript(f.read())

connection.close()
