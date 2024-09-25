DROP TABLE IF EXISTS contacts;

CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    phone TEXT NOT NULL,
    position TEXT,
    department TEXT,
    location TEXT
);

DROP TABLE IF EXISTS logs;

CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    action TEXT,
    ip_address TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(contact_id) REFERENCES contacts(id)
);
