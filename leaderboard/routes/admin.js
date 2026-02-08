const express = require('express');
const bcrypt = require('bcryptjs');
const db = require('../db');
const { sendApprovalEmail } = require('../email');

const router = express.Router();

// Auth middleware
function requireAdmin(req, res, next) {
  if (!req.session.adminId) {
    return res.redirect('/admin/login');
  }
  next();
}

// Login page
router.get('/login', (req, res) => {
  if (req.session.adminId) return res.redirect('/admin');
  res.render('admin-login', { error: null });
});

// Login handler
router.post('/login', (req, res) => {
  const { email, password } = req.body;

  const admin = db.prepare('SELECT * FROM admins WHERE email = ?').get(email);
  if (!admin || !bcrypt.compareSync(password, admin.password_hash)) {
    return res.render('admin-login', { error: 'Invalid email or password.' });
  }

  req.session.adminId = admin.id;
  res.redirect('/admin');
});

// Logout
router.get('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/');
});

// Dashboard
router.get('/', requireAdmin, (req, res) => {
  const filter = req.query.filter || 'pending';
  const validFilters = ['pending', 'approved', 'rejected'];
  const activeFilter = validFilters.includes(filter) ? filter : 'pending';

  const submissions = db.prepare(
    `SELECT * FROM submissions WHERE status = ? ORDER BY created_at DESC`
  ).all(activeFilter);

  const counts = {
    pending: db.prepare("SELECT COUNT(*) as c FROM submissions WHERE status = 'pending'").get().c,
    approved: db.prepare("SELECT COUNT(*) as c FROM submissions WHERE status = 'approved'").get().c,
    rejected: db.prepare("SELECT COUNT(*) as c FROM submissions WHERE status = 'rejected'").get().c,
  };

  res.render('admin-dashboard', { submissions, activeFilter, counts });
});

// Approve
router.post('/approve/:id', requireAdmin, async (req, res) => {
  const submission = db.prepare('SELECT * FROM submissions WHERE id = ?').get(req.params.id);
  if (!submission) return res.redirect('/admin');

  db.prepare(
    "UPDATE submissions SET status = 'approved', reviewed_at = datetime('now') WHERE id = ?"
  ).run(req.params.id);

  try {
    await sendApprovalEmail(submission);
  } catch (err) {
    console.error('[Email] Failed to send approval email:', err.message);
  }

  res.redirect('/admin?filter=pending');
});

// Reject
router.post('/reject/:id', requireAdmin, (req, res) => {
  db.prepare(
    "UPDATE submissions SET status = 'rejected', reviewed_at = datetime('now') WHERE id = ?"
  ).run(req.params.id);

  res.redirect('/admin?filter=pending');
});

// Delete
router.post('/delete/:id', requireAdmin, (req, res) => {
  const submission = db.prepare('SELECT photo_path FROM submissions WHERE id = ?').get(req.params.id);
  if (submission && submission.photo_path) {
    const fs = require('fs');
    const path = require('path');
    const filepath = path.join(__dirname, '..', 'public', 'uploads', submission.photo_path);
    fs.unlink(filepath, () => {});
  }

  db.prepare('DELETE FROM submissions WHERE id = ?').run(req.params.id);
  res.redirect('/admin');
});

module.exports = router;
