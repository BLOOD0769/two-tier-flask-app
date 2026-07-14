-- init.sql
-- This script runs automatically the FIRST time the MySQL container starts
-- (Docker mounts it into /docker-entrypoint-initdb.d/, which MySQL's
-- official image auto-executes on an empty database).
--
-- It creates the table our Flask app needs to store guestbook entries.

CREATE TABLE IF NOT EXISTS entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert one example row so the page isn't empty on first load
INSERT INTO entries (name, message) VALUES ('Jenkins', 'Deployed successfully via CI/CD pipeline!');
