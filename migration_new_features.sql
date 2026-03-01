-- ============================================
-- LexAI Migration: Add Contract Drafting & Legal Research tables
-- Run this in Supabase SQL Editor (if tables don't exist yet)
-- ============================================

-- 1. Create contract_drafts table
CREATE TABLE IF NOT EXISTS contract_drafts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  template_type TEXT NOT NULL,
  title TEXT NOT NULL,
  draft_content TEXT,
  form_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create legal_research_messages table
CREATE TABLE IF NOT EXISTS legal_research_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  legal_refs JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Enable RLS
ALTER TABLE contract_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE legal_research_messages ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policies
CREATE POLICY "Users can CRUD own contract drafts"
  ON contract_drafts FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can CRUD own legal research messages"
  ON legal_research_messages FOR ALL USING (auth.uid() = user_id);

-- 5. Create indexes
CREATE INDEX IF NOT EXISTS idx_contract_drafts_user_id ON contract_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_research_messages_user_id ON legal_research_messages(user_id);
