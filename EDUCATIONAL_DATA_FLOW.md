# Educational Data Flow Tracking

## Problem
Educational documents saved but `extracted_name` and `extracted_dob` columns are NULL in database.

## Data Flow With Logging

### 1. OCR (form.py:134)
Logs: `[Background OCR] Extracted X characters`

### 2. LLM Extraction (llm_extractor.py:195)
Logs to check:
- `[EDU-LLM] [STEP 1] Raw name value: ...`
- `[EDU-LLM] [STEP 1] Raw dob value: ...`

If None here → **LLM didn't find name/dob in marksheet**

### 3. Data Validation (form.py:143)
Logs to check:
- `[EDU_EXTRACTION_RESULT] name=...`
- `[EDU_EXTRACTION_RESULT] dob=...`
- `[EDU_EXTRACTION_RESULT] has_name=..., has_dob=...`

### 4. Database Save (crud.py:1465)
Logs to check:
- `[EDU+LLM SAVE] [STEP 2] Final validation:`
  `name_will_save=...`
  `dob_will_save=...`
- `[EDU+LLM SAVE] [STEP 5] Verified in database:`
  `saved_name=...`
  `saved_dob=...`

If saved values are None → check INSERT parameters

## Key Changes

1. **Enhanced LLM Prompt**: Now searches multiple locations on marksheet for name/dob
2. **Better Validation**: Detects and converts string "null" to actual None
3. **Detailed Logging**: 5-step tracking from dict to database
4. **Post-Insert Verification**: Reads back from database to confirm save
