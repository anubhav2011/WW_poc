-- Migration Script: Add Document Verification Columns
-- Purpose: Add verification fields to support name and DOB matching between personal and educational documents
-- Date: 2026-02-09

-- Add verification columns to workers table
ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending';
ALTER TABLE workers ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP DEFAULT NULL;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_name TEXT DEFAULT NULL;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS personal_extracted_dob TEXT DEFAULT NULL;

-- Add extraction and verification columns to educational_documents table
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS raw_ocr_text TEXT DEFAULT NULL;
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS llm_extracted_data TEXT DEFAULT NULL;
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_name TEXT DEFAULT NULL;
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS extracted_dob TEXT DEFAULT NULL;
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending';
ALTER TABLE educational_documents ADD COLUMN IF NOT EXISTS verification_errors TEXT DEFAULT NULL;

-- Create index for faster verification queries
CREATE INDEX IF NOT EXISTS idx_workers_verification_status ON workers(verification_status);
CREATE INDEX IF NOT EXISTS idx_educational_documents_verification ON educational_documents(worker_id, verification_status);
