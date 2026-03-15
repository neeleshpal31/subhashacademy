-- Database initialization script for Render
-- Auto-generated from college.db


-- Table: admissions
CREATE TABLE admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        course TEXT NOT NULL,
        message TEXT
    );
INSERT INTO admissions (id, name, email, phone, course, message) VALUES (1, 'DBTest_20260312191103', 'dbtest@example.com', '9999999999', 'BCA', 'Database test entry');
-- Table: admin
CREATE TABLE admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
INSERT INTO admin (id, username, password) VALUES (1, 'admin', 'scrypt:32768:8:1$4H0w6W9XI8xoc1Qf$6d639576cee06bacb52e57eb0b544f94939bbde667d95cda365ac147678ed2d5919d803f6b0ee158358efa40ac0471c92aa03f2aee962154d2cccb627f8cf351');
-- Table: gallery_images
CREATE TABLE gallery_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        filename TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    , category TEXT);
INSERT INTO gallery_images (id, title, description, filename, created_at, category) VALUES (1, '', '', 'a9edcdcda31144d59248349cc8ef819f.jpg', '2026-03-15 07:01:08', 'campus_infrastructure');