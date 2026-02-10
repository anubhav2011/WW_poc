# OCR to LLM Extraction Flow - Complete Guide

## Overview
This document explains how raw OCR text is extracted from documents and passed to LLM for structured data extraction.

## Complete Data Flow

### 1. OCR Extraction (ocr_service.py)
**Objective:** Extract complete raw text from documents (images/PDFs)

#### For Images (JPG, PNG, etc):
```
Image File → [PaddleOCR or Tesseract] → Raw OCR Text (complete)
```

**Logging Key Points:**
- `[RAW_OCR]` log shows first 500 characters of extracted text
- Logs character count: "Successfully extracted X characters"
- Both PaddleOCR and Tesseract fallback are logged

**Code Location:** `/vercel/share/v0-project/services/ocr_service.py:extract_text_from_image()`

#### For PDFs:
```
PDF File → [pdfplumber/PyPDF2] → Raw Text
                ↓ (if scanned PDF)
         [pdf2image] → Image → OCR → Raw Text
```

**Logging Key Points:**
- `[RAW_OCR]` log shows extracted text preview
- Character count logged for each page
- Fallback strategy logged if first method fails

**Code Location:** `/vercel/share/v0-project/services/ocr_service.py:extract_text_from_pdf()`

---

### 2. Data Passed to Extraction Functions

#### Personal Documents (form.py → ocr_cleaner.py):
```python
raw_ocr_text → clean_ocr_extraction() → Extracted fields:
{
    "name": "BABU KHAN",
    "dob": "01-12-1987",
    "address": "Full address"
}
```

#### Educational Documents (form.py → education_ocr_cleaner.py):
```python
raw_ocr_text → clean_education_ocr_extraction() → Extracted fields:
{
    "name": "BABU KHAN",              # ← NEW: For verification
    "dob": "01-12-1987",              # ← NEW: For verification
    "qualification": "Class 10",
    "board": "CBSE",
    "year_of_passing": "2017",
    "school_name": "ST DON BOSCO",
    "stream": "Science",
    "marks_type": "Percentage",
    "marks": "85%"
}
```

---

### 3. Educational Document Extraction Pipeline

#### Step 1: Rule-Based Extraction (ocr_cleaner.py)
```python
raw_ocr_text → rule_based_education_extraction()
├── Extract Name: Regex pattern matching for "Name:", "Student Name:", etc.
├── Extract DOB: Regex pattern for dates (DD-MM-YYYY, DD/MM/YYYY)
├── Extract Qualification: Pattern matching for "Class 10", "Class 12", degree names
├── Extract Board: Pattern matching for "CBSE", "ICSE", etc.
├── Extract Year: Pattern matching for 4-digit years
├── Extract School: Pattern matching for institution names
├── Extract Stream: Pattern matching for "Science", "Commerce", etc.
└── Extract Marks: Percentage or CGPA extraction
```

**Logging Output:**
```
[RULE-BASED] Extracted: name='BABU KHAN', dob='01-12-1987'
Rule-based extraction results - Name: True, DOB: True, Qualification: True, Year: True, School: True
```

#### Step 2: LLM Extraction (if rule-based incomplete)
```python
raw_ocr_text + EDUCATION_EXTRACTION_PROMPT → OpenAI GPT-4o-mini → JSON Response

Prompt includes:
- Critical fields instruction for name and DOB
- All educational fields required
- Search location hints (where to find name, DOB in document)
- Format specifications
```

**Prompt Key Instructions:**
```
CRITICAL FIELDS (MUST EXTRACT FOR VERIFICATION):
1. name: Student's full name EXACTLY as printed on document
2. dob: Date of birth in DD-MM-YYYY format

EDUCATIONAL FIELDS:
3-9. Qualification, Board, Year, School, Stream, Marks Type, Marks
```

**Logging Output:**
```
[OPENAI] Extracted: name='BABU KHAN', dob='01-12-1987'
[MERGE] Using OpenAI value for name: 'BABU KHAN'
[FINAL] Education extraction result: name='BABU KHAN', dob='01-12-1987'
```

#### Step 3: Validation & Storage (form.py → crud.py)
```python
edu_data with name & dob → save_educational_document_with_llm_data()
                         ↓
        Database INSERT:
        extracted_name = edu_data['name']     # → 'BABU KHAN'
        extracted_dob = edu_data['dob']       # → '01-12-1987'
```

**Logging Output:**
```
[EDU+LLM SAVE] [STEP 0] Raw dict values:
               name from dict: 'BABU KHAN'
               dob from dict: '01-12-1987'

[EDU+LLM SAVE] [STEP 5] Verified in database:
               saved_name='BABU KHAN' (is_null=False)
               saved_dob='01-12-1987' (is_null=False)
```

---

### 4. Verification Step

After both documents extracted:
```
Personal: name='BABU KHAN', dob='01-12-1987'
Educational: name='BABU KHAN', dob='01-12-1987'
        ↓
    Compare (fuzzy match for name, exact for dob)
        ↓
If matches: ✓ Verification Successful
If mismatch: ✗ Error: "Your details are not matching"
```

---

## Log Tracking Checklist

### 1. OCR Extraction Phase
Check logs for:
```
[RAW_OCR] PaddleOCR extracted text (first 500 chars): ...
OCR text length: X characters
Successfully extracted X characters
```

### 2. Rule-Based Extraction Phase
Check logs for:
```
[RULE-BASED] Extracted: name='...', dob='...'
Rule-based extraction results - Name: True/False, DOB: True/False
```

### 3. LLM Extraction Phase (if triggered)
Check logs for:
```
Attempting OpenAI extraction...
[OPENAI] Extracted: name='...', dob='...'
```

### 4. Storage Phase
Check logs for:
```
[EDU+LLM SAVE] [STEP 0] Raw dict values:
[EDU+LLM SAVE] [STEP 5] Verified in database:
               saved_name='...' (is_null=False)
               saved_dob='...' (is_null=False)
```

### 5. Verification Phase
Check logs for:
```
Personal data: name='...', dob='...'
[VERIFICATION] Retrieved X educational documents from database
✓✓✓ VERIFICATION SUCCESSFUL
or
✗✗✗ VERIFICATION FAILED
```

---

## Troubleshooting

### Problem: name/dob showing as NULL in database

**Check These in Order:**

1. **OCR Extraction**
   - Look for `[RAW_OCR]` logs
   - Is the raw text complete and readable?
   - OCR character count > 100?

2. **Rule-Based Extraction**
   - Look for `[RULE-BASED] Extracted: name=...`
   - If name/dob missing, LLM will be triggered
   - Check OpenAI logs for `[OPENAI] Extracted: name=...`

3. **Data Before Database**
   - Look for `[EDU+LLM SAVE] [STEP 0]` 
   - Is name/dob present before saving?
   - Check `[EDU+LLM SAVE] [STEP 4]` - values passed to INSERT

4. **Database Verification**
   - Look for `[EDU+LLM SAVE] [STEP 5]`
   - Does it show `saved_name=...` (not None)?
   - Query database directly to verify

### Problem: LLM not extracting name/dob

**Solutions:**
1. Check if LLM is even being called (look for "Attempting OpenAI extraction")
2. Verify OPENAI_API_KEY is set
3. Check LLM response in logs (look for JSON parsing errors)
4. Ensure OCR text contains readable name and DOB

---

## Key Files

| File | Purpose |
|------|---------|
| `/services/ocr_service.py` | Extracts raw OCR text from documents |
| `/services/education_ocr_cleaner.py` | Extracts structured data from educational docs |
| `/services/ocr_cleaner.py` | Extracts data from personal documents |
| `/api/form.py` | Orchestrates extraction and storage workflow |
| `/db/crud.py` | Saves extracted data to database |
| `/services/document_verifier.py` | Compares personal vs educational data |
