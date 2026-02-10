# LLM Data Extraction Implementation

This document explains the LLM-based data extraction system that has been implemented to extract personal and educational information from documents.

## Overview

The system now uses OpenAI's GPT models (via LLM) to intelligently extract structured data from OCR text, replacing the old regex-based extraction methods. This provides better accuracy and handles variations in document formats.

## Key Components

### 1. **LLM Extractor Service** (`services/llm_extractor.py`)

This module contains the core LLM extraction logic:

- `extract_personal_data_llm(raw_ocr_text)` - Extracts personal information (name, DOB, address, mobile) from identity documents
- `extract_educational_data_llm(raw_ocr_text)` - Extracts educational information (qualification, board, marks, etc.) from marksheets
- `call_llm_with_retry(prompt, system_prompt)` - Handles OpenAI API calls with retry logic
- `normalize_date_format(date_str)` - Converts dates to DD-MM-YYYY format

**Features:**
- Structured JSON extraction with proper schema validation
- Retry logic for API failures (max 3 attempts)
- Fallback error handling
- Date format normalization

### 2. **Updated Form API** (`api/form.py`)

The background OCR processing now uses LLM extraction:

**Changes:**
- `process_ocr_background()` now calls `extract_personal_data_llm()` instead of `clean_ocr_extraction()`
- `process_ocr_background()` now calls `extract_educational_data_llm()` instead of `clean_education_ocr_extraction()`
- Fallback to old cleaners if LLM extraction fails
- Saves raw OCR text and LLM extracted data to database for audit trail

### 3. **Database Updates** (`db/crud.py`)

**New Functions:**
- `update_worker_ocr_data()` - Saves raw OCR text and LLM extracted data to workers table
- Fixed bug in `get_worker_extraction_status()` - Was calling `fetchone()` twice

**New Database Columns (added in database.py):**
- `raw_ocr_text` - Raw OCR output before LLM processing
- `llm_extracted_data` - Full JSON response from LLM
- `extracted_name` - Name extracted from document
- `extracted_dob` - Date of birth extracted from document
- `verification_status` - Document verification state
- `verification_errors` - Any errors during verification

### 4. **OCR Service Fixes** (`services/ocr_service.py`)

**Fixed:**
- File locking issue during PDF to image conversion for scanned PDFs
- Improved temporary file handling with proper cleanup and retry logic
- Added delay to ensure files are written before processing

## Data Flow

```
1. Document Upload
    ↓
2. OCR Processing (PaddleOCR/Tesseract)
    ↓
3. Raw OCR Text → LLM (OpenAI)
    ↓
4. Structured JSON Extraction
    ↓
5. Save to Database + Verify
    ↓
6. Name/DOB Matching Between Documents
```

## Environment Variables Required

```env
OPENAI_API_KEY=sk-xxx...  # Required for LLM extraction
LLM_MODEL=gpt-4o-mini     # Default model (can be changed)
```

## Example Extracted Data

### Personal Document Extraction:
```json
{
    "name": "BABU KHAN",
    "dob": "01-12-1987",
    "address": "KAMLA RAMAN NAGAR...",
    "mobile": "7905285898"
}
```

### Educational Document Extraction:
```json
{
    "name": "BABU KHAN",
    "dob": "01-12-1987",
    "document_type": "marksheet",
    "qualification": "Class 10",
    "board": "CBSE",
    "stream": null,
    "year_of_passing": "2017",
    "school_name": "ST DON BOSCO COLLEGE",
    "marks_type": "CGPA",
    "marks": "07.4 CGPA"
}
```

## Verification Process

After extracting data:
1. Personal document data is saved with extracted name and DOB
2. Educational documents are also processed and saved
3. Name and DOB from educational documents are compared with personal document
4. Verification status is updated (verified/failed/pending)
5. Mismatches are logged for manual review

## Troubleshooting

### OCR Extraction Failing
- Check logs for OCR library availability (PaddleOCR/Tesseract)
- Ensure document images are clear and readable
- Verify file permissions are correct

### LLM Extraction Failing
- Verify `OPENAI_API_KEY` is set correctly
- Check OpenAI API quota and rate limits
- Review LLM error messages in logs
- System will fallback to old extraction methods if LLM fails

### Document Verification Failing
- Check that name and DOB match between documents
- Review verification error details in logs
- Ensure documents are genuine and from same person

## Testing

To test LLM extraction:

1. Upload a personal document (PDF/PNG) containing name and DOB
2. Upload educational documents (marksheets)
3. Check logs for:
   - OCR extraction success
   - LLM extraction with field values
   - Verification matching results

Look for log entries like:
```
[Background OCR] ✓ LLM extracted personal data: name=BABU KHAN, dob=01-12-1987
[Background OCR] ✓ LLM extracted educational data: name=BABU KHAN, qualification=Class 10, dob=01-12-1987
```

## Future Improvements

- Cache LLM responses for identical OCR inputs
- Implement confidence scoring for extractions
- Add batch LLM processing for multiple documents
- Support additional document types (passport, visa, etc.)
- Implement fuzzy matching for name verification
