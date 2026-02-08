require('dotenv').config();
const express = require('express');
const session = require('express-session');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3000;

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/uploads', express.static(path.join(__dirname, 'public', 'uploads')));

app.use(session({
  secret: process.env.SESSION_SECRET || 'change-me',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 },
}));

// Make session data available to all views
app.use((req, res, next) => {
  res.locals.isAdmin = !!req.session.adminId;
  next();
});

// Routes
app.use('/', require('./routes/public'));
app.use('/admin', require('./routes/admin'));

app.listen(PORT, () => {
  console.log(`Three Peaks Leaderboard running at http://localhost:${PORT}`);
});
