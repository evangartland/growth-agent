# Three Peaks Challenge — Shopify Version

A leaderboard you can paste directly into a Shopify page. Uses [Supabase](https://supabase.com) (free tier) as the backend.

## Setup (5 minutes)

### Step 1: Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and sign up (free)
2. Click **New Project**, pick a name and password, choose a region close to you
3. Wait for the project to be created (~30 seconds)

### Step 2: Run the database setup

1. In your Supabase project, go to **SQL Editor** (left sidebar)
2. Click **New Query**
3. Paste the entire contents of **`setup.sql`** from this folder
4. Click **Run** — you should see "Success. No rows returned"

### Step 3: Create your admin user

1. Go to **Authentication** → **Users** (left sidebar)
2. Click **Add User** → **Create New User**
3. Enter your email and a password — this is your admin login

### Step 4: Get your API keys

1. Go to **Settings** → **API** (left sidebar)
2. Copy the **Project URL** (looks like `https://abcdefg.supabase.co`)
3. Copy the **anon public** key (the long string)

### Step 5: Add the leaderboard to Shopify

1. Open **`shopify-embed.html`** in a text editor
2. Near the bottom, replace the two placeholder values:
   ```js
   const SUPABASE_URL = 'https://your-project.supabase.co';
   const SUPABASE_ANON_KEY = 'your-anon-key-here';
   ```
3. In Shopify: **Online Store** → **Pages** → **Add Page**
4. Click the **`<>`** button (Show HTML) in the editor
5. Paste the entire contents of `shopify-embed.html`
6. Save the page

### Step 6: Set up the admin panel

1. Open **`admin.html`** in a text editor
2. Replace the same two values (`SUPABASE_URL` and `SUPABASE_ANON_KEY`)
3. Save the file and open it in your browser (just double-click it)
4. Log in with the email/password from Step 3
5. Bookmark it for easy access

## How It Works

| What | Where |
|---|---|
| Leaderboard + submit form | Pasted into a Shopify page |
| Database + photo storage | Supabase (free tier) |
| Admin approval | `admin.html` opened in your browser |
| Data stays | In your Supabase project, you own it |

## Files

| File | Purpose |
|---|---|
| `setup.sql` | Creates the database table, security policies, and storage bucket. Run once in Supabase SQL Editor. |
| `shopify-embed.html` | The leaderboard + submission form. Paste into a Shopify page. |
| `admin.html` | Admin panel to approve/reject submissions. Open locally in your browser. |

## Security

- The Supabase **anon key** is safe to include in public HTML — it can only read approved submissions and insert new pending ones
- The admin panel requires email/password authentication
- Row Level Security (RLS) ensures unauthenticated users cannot approve, reject, or delete submissions
- Photo uploads are limited to the `photos` storage bucket

## Email Notifications

To send emails when a submission is approved, you can set up a Supabase Edge Function or a [Zapier](https://zapier.com) / [Make](https://make.com) integration that triggers when a row's `status` changes to `approved`. This is optional and not included in the base setup.
