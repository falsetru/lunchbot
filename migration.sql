-- How to run: sqlite3 lunch.sqlite < migration.sql
ALTER TABLE menu ADD restaurant TEXT;
UPDATE menu SET restaurant = 'hsd';
