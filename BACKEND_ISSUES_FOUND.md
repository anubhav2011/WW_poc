# Backend Logic Issues Found

## Critical Issues

### 1. **Missing Raw OCR Text Logging in form.py** ❌
**Location:** `api/form.py` - Line 71-80 (personal document processing)

**Problem:** The raw OCR text is extracted but not logged with `[RAW_OCR]` prefix to show what's being passed to LLM.

**Impact:** Cannot verify if complete raw text from document is being passed to LLM.

**Fix Required:**
```python
# After: personal_ocr_text = await loop.run_in_executor(None, ocr_to_text, personal_doc_path)
logger.info(f"[RAW_OCR] PERSONAL document text (first 500 chars): {personal_ocr_text[:500]}")
logger.info(f"[RAW_OCR] PERSONAL document total: {len(personal_ocr_text)} characters")
```

---

### 2. **Educational OCR Text Not Logged** ❌
**Location:** `api/form.py` - Line ~120-130 (educational document processing)

**Problem:** Same issue - raw OCR text from educational documents is not logged.

**Impact:** Cannot trace if raw educational document text is complete.

**Fix Required:**
```python
# After: edu_ocr_text = await loop.run_in_executor(None, ocr_to_text, edu_doc_path)
logger.info(f"[RAW_OCR] EDUCATIONAL doc text (first 500 chars): {edu_ocr_text[:500]}")
logger.info(f"[RAW_OCR] EDUCATIONAL doc total: {len(edu_ocr_text)} characters")
```

---

### 3. **Unnecessary Rule-Based Extraction Layer** ⚠️
**Location:** `api/form.py` - Uses `clean_education_ocr_extraction()` which applies rule-based extraction

**Problem:** Educational documents use BOTH rule-based extraction AND LLM extraction. This adds redundant processing and may extract incomplete data via rules instead of using LLM fully.

**Current Flow:**
```
OCR Text → clean_education_ocr_extraction() → rule-based extraction first → then LLM if rules fail → save to DB
```

**Should Be:**
```
OCR Text → Pass directly to LLM → save to DB (skip rule-based for consistency)
```

**Impact:** LLM may not get a chance to extract if rule-based extraction provides partial results.

**Fix:** Remove rule-based extraction for educational documents, pass raw OCR directly to LLM.

---

### 4. **Personal Document Missing LLM Extraction** ❌
**Location:** `api/form.py` - Line 81

**Problem:** Personal document uses `extract_personal_data_llm()` correctly, but there's also `clean_ocr_extraction()` being used. Verify which is actually being called.

**Check Required:** Ensure `extract_personal_data_llm()` receives raw OCR text and passes it to LLM, not to rule-based cleaner first.

---

### 5. **Verification Fails When Educational DOB is NULL** ❌
**Location:** `services/document_verifier.py` - Line 228-237

**Problem:** If `extracted_name` or `extracted_dob` from educational document is NULL/empty, verification returns "pending" instead of attempting partial verification.

```python
if not personal_name or not personal_dob:
    logger.error("Personal document data incomplete - cannot verify")
    return {"status": "pending", ...}
```

**Impact:** If LLM doesn't extract DOB from educational doc, verification status stays "pending" forever.

**Fix Required:** Log what values are missing and provide better error messaging. Allow verification to proceed if at least name or school matches.

---

### 6. **Database Query Missing Row ID in Retrieval** ⚠️
**Location:** `db/crud.py` - Line 1716 (`get_educational_documents_for_verification`)

**Problem:** Query retrieves columns in order: `id, qualification, extracted_name, extracted_dob, verification_status` but doesn't include all needed fields for debugging (like `school_name`, `board`).

**Impact:** When verification fails, we can't see which school's document failed - only the qualification.

**Fix:** Add `school_name` and `board` to the SELECT query for better error messages.

---

## Medium Priority Issues

### 7. **No Validation of LLM Response Structure** ⚠️
**Location:** `services/llm_extractor.py` - Line 100-102

**Problem:** After JSON parse succeeds, code doesn't validate that all required fields exist in the response.

**Example:** If LLM returns `{"qualification": "...", "marks": "..."}` but missing `name` and `dob`, code doesn't catch this.

**Fix:** Add validation after JSON parsing:
```python
required_fields = ["name", "dob", "qualification", "board", ...]
if not all(field in data for field in required_fields):
    logger.error(f"Missing required fields: {[f for f in required_fields if f not in data]}")
    # Handle gracefully
```

---

### 8. **Error Handling Missing in Document Processing** ⚠️
**Location:** `api/form.py` - Line 120-150 (educational doc loop)

**Problem:** If one educational document fails to save, the entire loop continues without recording which document failed.

**Fix:** Wrap each educational document save in try-catch and log failures clearly.

---

## Summary

**Critical Fixes Needed:**
1. Add raw OCR text logging for both personal and educational documents
2. Remove rule-based extraction layer - pass raw OCR directly to LLM for educational docs
3. Improve verification error handling when DOB is missing
4. Add field validation after LLM JSON parsing
5. Add `school_name` and `board` to educational document retrieval query

**Testing After Fixes:**
- Upload a personal document and check logs for `[RAW_OCR]` showing complete text
- Upload an educational document and check logs for `[RAW_OCR]` showing complete text
- Verify that LLM receives the full raw text, not filtered results
- Check database to confirm `extracted_name` and `extracted_dob` are populated
- Test verification with various name/DOB combinations

