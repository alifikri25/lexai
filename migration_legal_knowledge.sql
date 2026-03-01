-- ============================================
-- LexAI Migration: Legal Knowledge Base (RAG)
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Create legal_knowledge_base table for UU chunks
CREATE TABLE IF NOT EXISTS legal_knowledge_base (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_file TEXT,
  chunk_text TEXT NOT NULL,
  chunk_index INTEGER,
  embedding vector(384),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Enable RLS
ALTER TABLE legal_knowledge_base ENABLE ROW LEVEL SECURITY;

-- 3. Policy: allow all authenticated users to read
CREATE POLICY "Authenticated users can read legal knowledge"
  ON legal_knowledge_base FOR SELECT
  USING (auth.role() = 'authenticated');

-- 4. Policy: only service role can insert/update/delete
CREATE POLICY "Service role can manage legal knowledge"
  ON legal_knowledge_base FOR ALL
  USING (auth.role() = 'service_role');

-- 5. Create index for performance
CREATE INDEX IF NOT EXISTS idx_legal_knowledge_base_source ON legal_knowledge_base(source_name);
