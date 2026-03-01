-- ============================================
-- LexAI Migration: Legal Research Sessions
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Create sessions table
CREATE TABLE IF NOT EXISTS legal_research_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'Riset Baru',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add session_id column to messages
ALTER TABLE legal_research_messages
  ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES legal_research_sessions(id) ON DELETE CASCADE;

-- 3. Enable RLS
ALTER TABLE legal_research_sessions ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policy
CREATE POLICY "Users can CRUD own sessions"
  ON legal_research_sessions FOR ALL USING (auth.uid() = user_id);

-- 5. Create indexes
CREATE INDEX IF NOT EXISTS idx_legal_research_sessions_user_id ON legal_research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_research_messages_session_id ON legal_research_messages(session_id);
