# Educational Document Name & DOB Save - Debug Guide

## Overview
This document traces how name and DOB are extracted from educational documents and saved to the database.

## Data Flow

### 1. LLM Extraction (`services/llm_extractor.py`)
```
Raw OCR Text → call_llm_with_retry() → JSON Parse → extract_educational_data_llm()
```

**Key Logging:**
- `[EDU-LLM] [STEP 1]` - Raw LLM response with all keys
- `[EDU-LLM] [STEP 1]` - Raw name/dob values extracted from response
- `[EDU-LLM] [STEP 2]` - After normalization (DOB format, qualification normalize)
- `[EDU-LLM] [FINAL]` - Final extracted data before return

**Expected Output Example:**
```
[EDU-LLM] [STEP 1] LLM returned result with keys: ['name', 'dob', 'qualification', ...]
[EDU-LLM] [STEP 1] Raw name value: 'ANANYA SHARMA' (type: str)
[EDU-LLM] [STEP 1] Raw dob value: '05-06-1998' (type: str)
[EDU-LLM] [FINAL] ✓ Educational data extracted successfully:
[EDU-LLM]         name='ANANYA SHARMA'
[EDU-LLM]         dob='05-06-1998'
```

### 2. Data Passing to Save (`api/form.py`)
```
extract_educational_data_llm() → edu_data dict → save_educational_document_with_llm_data()
```

**Key Logging:**
- `[EXTRACTION_CHECK]` - Validates edu_data received with name/dob fields
- Shows exact values and whether they are None

**Expected Output Example:**
```
[EXTRACTION_CHECK] LLM returned edu_data with keys: ['name', 'dob', ...]
[EXTRACTION_CHECK] name field: 'ANANYA SHARMA' (is_none=False)
[EXTRACTION_CHECK] dob field: '05-06-1998' (is_none=False)
```

### 3. Database Save (`db/crud.py` - `save_educational_document_with_llm_data()`)

**Step 1: Extraction from Dict**
```
[EDU+LLM SAVE] [STEP 1] Raw extracted_name from dict: 'ANANYA SHARMA' (type: str)
[EDU+LLM SAVE] [STEP 1] Raw extracted_dob from dict: '05-06-1998' (type: str)
```

**Step 2: String Validation**
```
[EDU+LLM SAVE] [STEP 2] After string conversion & strip:
[EDU+LLM SAVE]          extracted_name='ANANYA SHARMA' (type: str)
[EDU+LLM SAVE]          extracted_dob='05-06-1998' (type: str)
```

**Step 3: Null Checks**
```
[EDU+LLM SAVE] [STEP 3] Final null checks:
[EDU+LLM SAVE]          name_is_null=False, name_empty=False
[EDU+LLM SAVE]          dob_is_null=False, dob_empty=False
```

**Step 4: INSERT Statement**
```
[EDU+LLM SAVE] [STEP 4] INSERT executed, values passed to DB:
[EDU+LLM SAVE]          extracted_name param='ANANYA SHARMA'
[EDU+LLM SAVE]          extracted_dob param='05-06-1998'
```

**Step 5: Verification Read**
```
[EDU+LLM SAVE] [STEP 5] ✓ Verified in database:
[EDU+LLM SAVE]          doc_id=123
[EDU+LLM SAVE]          saved_name='ANANYA SHARMA' (is_null=False)
[EDU+LLM SAVE]          saved_dob='05-06-1998' (is_null=False)
[EDU+LLM SAVE]          status=pending
```

## Troubleshooting Checklist

### If Name/DOB shows as None in STEP 1:
1. Check LLM response - may not have extracted name/dob
2. Check OCR quality - document may be too blurry/unclear
3. Check LLM prompt - ensure it has clear instructions for name/dob extraction

### If Name/DOB shows as None in STEP 2:
1. Check if value was empty string that got stripped
2. Check if value was all whitespace

### If Name/DOB shows as None in STEP 5 (database):
1. INSERT statement may have explicit `None` conversion
2. Check SQL parameter binding - may not have passed value correctly
3. Check database column type - ensure TEXT/VARCHAR type

### If verification still fails:
1. Check that BOTH steps 5 show non-null values for name and dob
2. Check `verification_status` is set to 'pending' (not 'failed')
3. Run: `SELECT extracted_name, extracted_dob FROM educational_documents WHERE worker_id = ?`
4. Verify values match personal document exactly

## Database Query for Verification

```sql
-- Check what's actually saved
SELECT 
    id,
    worker_id,
    qualification,
    extracted_name,
    extracted_dob,
    verification_status
FROM educational_documents
WHERE worker_id = ?
ORDER BY id DESC;
```

Expected output should show `extracted_name` and `extracted_dob` populated with actual values.

## Key Success Criteria

✓ All 5 steps show non-null values for name and dob
✓ STEP 5 verification confirms values in database
✓ Database query shows extracted_name and extracted_dob populated
✓ Verification runs (not skipped) with these values
