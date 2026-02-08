const express = require('express');
const multer = require('multer');
const path = require('path');
const db = require('../db');

const router = express.Router();

// Configure multer for photo uploads
const storage = multer.diskStorage({
  destination: path.join(__dirname, '..', 'public', 'uploads'),
  filename: (req, file, cb) => {
    const unique = Date.now() + '-' + Math.round(Math.random() * 1e9);
    const ext = path.extname(file.originalname);
    cb(null, unique + ext);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: (req, file, cb) => {
    const allowed = /jpeg|jpg|png|webp/;
    const extOk = allowed.test(path.extname(file.originalname).toLowerCase());
    const mimeOk = allowed.test(file.mimetype);
    cb(null, extOk && mimeOk);
  },
});

// Leaderboard (home)
router.get('/', (req, res) => {
  const submissions = db.prepare(
    `SELECT id, name, hours, minutes, seconds, total_seconds, photo_path, created_at
     FROM submissions
     WHERE status = 'approved'
     ORDER BY total_seconds ASC`
  ).all();

  res.render('leaderboard', { submissions });
});

// Submit form
router.get('/submit', (req, res) => {
  res.render('submit', { error: null, success: false });
});

// Handle submission
router.post('/submit', upload.single('photo'), (req, res) => {
  const { name, email, hours, minutes, seconds } = req.body;

  // Validate
  if (!name || !email || hours === undefined || minutes === undefined || seconds === undefined) {
    return res.render('submit', { error: 'All fields are required.', success: false });
  }

  const h = parseInt(hours, 10);
  const m = parseInt(minutes, 10);
  const s = parseInt(seconds, 10);

  if (isNaN(h) || isNaN(m) || isNaN(s) || h < 0 || m < 0 || m > 59 || s < 0 || s > 59) {
    return res.render('submit', { error: 'Please enter a valid completion time.', success: false });
  }

  const totalSeconds = h * 3600 + m * 60 + s;
  const photoPath = req.file ? req.file.filename : null;

  db.prepare(
    `INSERT INTO submissions (name, email, hours, minutes, seconds, total_seconds, photo_path)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).run(name, email, h, m, s, totalSeconds, photoPath);

  res.render('submit', { error: null, success: true });
});

module.exports = router;
