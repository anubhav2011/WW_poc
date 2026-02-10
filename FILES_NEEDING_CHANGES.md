# Files Needing Changes - Educational Document OCR/LLM Extraction Fix

## Critical Issues Identified from Debug Logs

### Issue 1: Missing Columns in Database Tables
**Error from Logs:** `ERROR - no such column: raw_ocr_text`

The workers table is missing columns for storing raw OCR data and extracted name/dob from educational documents.
The educational_documents table is missing columns for raw_ocr_text, extracted_name, extracted_dob, llm_extracted_data, and verification_status.

---

## Files That Need Changes

### 1. **`/vercel/share/v0-project/db/database.py`** - DATABASE SCHEMA
**Status:** NEEDS CHANGES
**Issues:**
- Line 86-96: Workers table missing columns:
  - `personal_extracted_name` (for personal doc name)
  - `personal_extracted_dob` (for personal doc dob)
  - `verification_status` (to track verification state)

- Line 186-201: Educational documents table missing critical columns:
  - `extracted_name` - Student name from marksheet (MANDATORY)
  - `extracted_dob` - Student DOB from marksheet (MANDATORY)
  - `raw_ocr_text` - Complete raw OCR text from document
  - `llm_extracted_data` - Full JSON response from LLM
  - `verification_status` - Track if verified/failed/pending

**Fix Required:**
```sql
ALTER TABLE workers ADD COLUMN personal_extracted_name TEXT;
ALTER TABLE workers ADD COLUMN personal_extracted_dob TEXT;
ALTER TABLE workers ADD COLUMN verification_status TEXT DEFAULT 'pending';

ALTER TABLE educational_documents ADD COLUMN extracted_name TEXT;
ALTER TABLE educational_documents ADD COLUMN extracted_dob TEXT;
ALTER TABLE educational_documents ADD COLUMN raw_ocr_text TEXT;
ALTER TABLE educational_documents ADD COLUMN llm_extracted_data TEXT;
ALTER TABLE educational_documents ADD COLUMN verification_status TEXT DEFAULT 'pending';
```

---

### 2. **`/vercel/share/v0-project/db/crud.py`** - DATABASE CRUD OPERATIONS
**Status:** NEEDS CHANGES
**Issues:**
- Function `update_worker_ocr_data()` tries to update `raw_ocr_text` and `llm_extracted_data` columns that don't exist in workers table
- Missing function to save educational document with name and dob
- Missing function to verify extracted name/dob against personal document

**Functions to Fix/Add:**
1. Fix `update_worker_ocr_data()` - Remove references to non-existent columns or create them
2. Add/Fix `save_educational_document_with_llm_data()` - Must save extracted_name and extracted_dob
3. Fix `get_worker_extraction_status()` - Should query extracted_name and extracted_dob columns
4. Add `update_educational_document_verification()` - Update verification status after comparison
5. Add `get_educational_documents_for_verification()` - Get docs to verify against personal data

---

### 3. **`/vercel/share/v0-project/api/form.py`** - OCR PROCESSING FLOW
**Status:** NEEDS CHANGES
**Issues:**
- Line ~85: Educational documents are found but NOT being processed for OCR/LLM extraction
- No code to extract raw text from educational documents and pass to LLM
- No code to extract name and dob from educational documents
- No verification logic comparing educational doc data with personal doc data
- No user feedback when verification fails

**Flow Missing:**
1. When educational document is uploaded, trigger OCR extraction
2. Extract COMPLETE raw OCR text from educational document
3. Pass raw text to LLM for structured extraction
4. Extract name and dob from LLM response (make them MANDATORY)
5. Save to educational_documents table with extracted_name and extracted_dob
6. Compare with personal document data
7. If match: show OCR text and proceed
8. If no match: tell user to reupload

---

### 4. **`/vercel/share/v0-project/services/llm_extractor.py`** - LLM EXTRACTION
**Status:** PARTIALLY WORKING - NEEDS VERIFICATION
**Issues:**
- Function `extract_educational_data_llm()` exists but may not be called for educational documents
- Prompt may not be aggressive enough about extracting name and dob

**Verification Needed:**
- Confirm the prompt explicitly requires name and dob extraction
- Ensure function returns structured JSON with name, dob, and other fields
- Add error handling if name/dob are missing from response

---

### 5. **`/vercel/share/v0-project/services/education_ocr_cleaner.py`** - EDUCATION OCR CLEANING
**Status:** PARTIALLY WORKING - NEEDS VERIFICATION
**Issues:**
- Function `clean_education_ocr_extraction()` may exist but verification needed
- Must ensure complete raw OCR text is passed to LLM
- Must ensure name and dob are extracted

**Verification Needed:**
- Check if complete raw OCR text is being passed
- Confirm name/dob extraction is mandatory
- Verify fallback to LLM if rule-based extraction fails

---

### 6. **`/vercel/share/v0-project/services/ocr_service.py`** - OCR EXTRACTION
**Status:** WORKING - NO CHANGES NEEDED
- `extract_text_from_image()` and `extract_text_from_pdf()` extract complete raw text
- Logging is adequate

---

## Implementation Order

1. **FIRST:** Update `db/database.py` - Add missing columns to workers and educational_documents tables
2. **SECOND:** Update `db/crud.py` - Fix CRUD operations to use correct columns and add missing functions
3. **THIRD:** Update `api/form.py` - Add educational document OCR processing flow
4. **FOURTH:** Verify `services/llm_extractor.py` - Ensure name/dob extraction is mandatory
5. **FIFTH:** Verify `services/education_ocr_cleaner.py` - Ensure complete raw text is processed

---

## Critical Requirements

✓ When educational document uploaded:
  1. Extract ALL raw OCR text completely
  2. Pass complete raw text to LLM
  3. LLM extracts: name (MANDATORY), dob (MANDATORY), and other fields
  4. Save extracted_name and extracted_dob to database
  5. Compare with personal document
  6. If match: Show OCR text and proceed
  7. If mismatch: Tell user "Document verification failed. Please reupload the document."

