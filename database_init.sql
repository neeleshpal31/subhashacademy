-- PostgreSQL initialization script for the college website

CREATE TABLE IF NOT EXISTS admissions (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    course TEXT NOT NULL,
    message TEXT
);

CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gallery_images (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    filename TEXT NOT NULL,
    category TEXT DEFAULT 'campus_infrastructure',
    image_data BYTEA,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO admin (id, username, password)
VALUES (1, 'admin', 'scrypt:32768:8:1$4H0w6W9XI8xoc1Qf$6d639576cee06bacb52e57eb0b544f94939bbde667d95cda365ac147678ed2d5919d803f6b0ee158358efa40ac0471c92aa03f2aee962154d2cccb627f8cf351')
ON CONFLICT (id) DO NOTHING;

INSERT INTO gallery_images (id, title, description, filename, created_at, category)
VALUES (1, 'Campus & Infrastructure 1', 'Campus & Infrastructure photo', 'a9edcdcda31144d59248349cc8ef819f.jpg', '2026-03-15 07:01:08', 'campus_infrastructure')
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('admissions', 'id'), COALESCE((SELECT MAX(id) FROM admissions), 1), true);
SELECT setval(pg_get_serial_sequence('admin', 'id'), COALESCE((SELECT MAX(id) FROM admin), 1), true);
SELECT setval(pg_get_serial_sequence('gallery_images', 'id'), COALESCE((SELECT MAX(id) FROM gallery_images), 1), true);