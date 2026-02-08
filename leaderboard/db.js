const Database = require('better-sqlite3');
const path = require('path');
const bcrypt = require('bcryptjs');

const DB_PATH = path.join(__dirname, 'data', 'leaderboard.db');

// Ensure data directory exists
const fs = require('fs');
fs.mkdirSync(path.join(__dirname, 'data'), { recursive: true });

const db = new Database(DB_PATH);

// Enable WAL mode for better concurrent read performance
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    hours INTEGER NOT NULL,
    minutes INTEGER NOT NULL,
    seconds INTEGER NOT NULL,
    total_seconds INTEGER NOT NULL,
    photo_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
  );

  CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
  );

  CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
  CREATE INDEX IF NOT EXISTS idx_submissions_total_seconds ON submissions(total_seconds);
`);

// Seed default admin if none exists
const adminCount = db.prepare('SELECT COUNT(*) as count FROM admins').get();
if (adminCount.count === 0) {
  const email = process.env.ADMIN_EMAIL || 'admin@threepeaks.com';
  const password = process.env.ADMIN_PASSWORD || 'admin123';
  const hash = bcrypt.hashSync(password, 10);
  db.prepare('INSERT INTO admins (email, password_hash) VALUES (?, ?)').run(email, hash);
}

module.exports = db;
