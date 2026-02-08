# Three Peaks Challenge Leaderboard

A self-contained leaderboard web app for the Three Peaks Challenge. Users submit their completion time and photo, an admin reviews submissions, and approved entries appear on a public leaderboard ranked by time.

## Features

- **Public leaderboard** ranked by completion time with medals for top 3
- **Submission form** with photo upload (JPEG/PNG/WebP, max 10MB)
- **Admin panel** with login, approve/reject queue, and submission management
- **Email notifications** sent to users when their submission is approved
- **Mobile-friendly** responsive design
- **SQLite database** - no external database required

## Quick Start

```bash
cd leaderboard
npm install
cp .env.example .env   # Edit with your settings
npm start              # Runs on http://localhost:3000
```

## Default Admin Credentials

- **Email:** `admin@threepeaks.com`
- **Password:** `admin123`

Change these in `.env` before deploying.

## Configuration (.env)

| Variable | Description |
|---|---|
| `PORT` | Server port (default: 3000) |
| `SESSION_SECRET` | Session encryption secret |
| `ADMIN_EMAIL` | Default admin login email |
| `ADMIN_PASSWORD` | Default admin password |
| `SMTP_HOST` | SMTP server for emails |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `EMAIL_FROM` | Sender email address |

## Project Structure

```
leaderboard/
  server.js          # Express app entry point
  db.js              # SQLite database setup
  email.js           # Email notification service
  routes/
    public.js        # Leaderboard & submission routes
    admin.js         # Admin authentication & management
  views/             # EJS templates
  public/
    css/styles.css   # All styles
    uploads/         # User-uploaded photos
```
