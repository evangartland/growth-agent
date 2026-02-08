-- ==============================================
-- Three Peaks Challenge Leaderboard
-- Run this in your Supabase SQL Editor (supabase.com → project → SQL Editor)
-- ==============================================

-- 1. Submissions table
CREATE TABLE submissions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  hours INT NOT NULL CHECK (hours >= 0),
  minutes INT NOT NULL CHECK (minutes >= 0 AND minutes <= 59),
  seconds INT NOT NULL CHECK (seconds >= 0 AND seconds <= 59),
  total_seconds INT NOT NULL,
  photo_url TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ
);

-- 2. Indexes
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_ranking ON submissions(status, total_seconds) WHERE status = 'approved';

-- 3. Row Level Security
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;

-- Anyone can view approved submissions (public leaderboard)
CREATE POLICY "Public can view approved submissions"
  ON submissions FOR SELECT
  USING (status = 'approved');

-- Anyone can submit a new entry
CREATE POLICY "Anyone can submit"
  ON submissions FOR INSERT
  WITH CHECK (status = 'pending');

-- Authenticated users (admin) can view all submissions
CREATE POLICY "Admin can view all"
  ON submissions FOR SELECT
  TO authenticated
  USING (true);

-- Authenticated users (admin) can update submissions
CREATE POLICY "Admin can update"
  ON submissions FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Authenticated users (admin) can delete submissions
CREATE POLICY "Admin can delete"
  ON submissions FOR DELETE
  TO authenticated
  USING (true);

-- 4. Storage bucket for photos
INSERT INTO storage.buckets (id, name, public)
VALUES ('photos', 'photos', true)
ON CONFLICT (id) DO NOTHING;

-- Anyone can upload photos
CREATE POLICY "Anyone can upload photos"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'photos');

-- Anyone can view photos
CREATE POLICY "Public photo access"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'photos');

-- Admin can delete photos
CREATE POLICY "Admin can delete photos"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (bucket_id = 'photos');
