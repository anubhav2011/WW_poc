# Document Verification Workflow

This document explains how the name and DOB verification works between personal and educational documents.

## Overview

The verification workflow follows these steps:

1. **User uploads personal document** → OCR + LLM extraction → Name and DOB extracted
2. **User uploads educational document** → OCR + LLM extraction → Name and DOB extracted
3. **User calls GET `/form/worker/{worker_id}/data`** → Verification runs automatically
4. **System compares** personal document data with each educational document
5. **Result**: 
   - If **MATCH** → Proceed to next step (upload more documents or move to experience collection)
   - If **MISMATCH** → User must re-upload correct documents

## Database Columns

### Workers Table
- `personal_extracted_name`: Extracted name from personal document (set during personal document upload)
- `personal_extracted_dob`: Extracted DOB from personal document (set during personal document upload)
- `verification_status`: Status of verification ('pending', 'verified', 'failed')
- `verified_at`: Timestamp when verification was completed
- `verification_errors`: JSON string containing mismatch details if verification failed

### Educational Documents Table
- `extracted_name`: Extracted name from this educational document
- `extracted_dob`: Extracted DOB from this educational document
- `verification_status`: Verification status for this specific document ('pending', 'verified', 'failed')
- `verification_errors`: Mismatch details for this document

## API Endpoints

### 1. Upload Personal Document
**POST** `/form/submit`
- Uploads personal document (Aadhaar, Passport, License, etc.)
- Triggers background OCR + LLM extraction
- Saves name, DOB to `workers.personal_extracted_name`, `personal_extracted_dob`

### 2. Upload Educational Document
**POST** `/form/submit`
- Uploads educational document (marksheet, certificate, etc.)
- Triggers background OCR + LLM extraction
- Saves name, DOB to `educational_documents.extracted_name`, `extracted_dob`

### 3. Get Worker Data (Triggers Verification)
**GET** `/form/worker/{worker_id}/data`
- Returns worker personal data and educational documents
- **Automatically triggers verification** if:
  - Personal document has been uploaded AND extracted
  - Educational documents have been uploaded AND extracted
  - Verification hasn't been run yet (verification_status still pending)

### Verification Response

**If Verification PASSES** (200 OK):
```json
{
  "status": "success",
  "worker": {
    "name": "John Doe",
    "dob": "01-01-1990",
    "verification_status": "verified",
    "verified_at": "2026-02-10T11:37:43Z"
  },
  "education": [
    {
      "id": 1,
      "qualification": "Class 10",
      "extracted_name": "John Doe",
      "extracted_dob": "01-01-1990",
      "verification_status": "verified"
    }
  ],
  "message": "All data verified successfully. Proceed to next step."
}
```

**If Verification FAILS** (400 Bad Request):
```json
{
  "statusCode": 400,
  "responseData": {
    "status": "verification_failed",
    "message": "Document verification failed. Please re-upload correct documents.",
    "verification": {
      "overall_status": "failed",
      "mismatches": [
        {
          "document_id": 1,
          "field": "name",
          "reason": "Mismatch: 'John Doe' (personal) != 'Jon Doe' (educational)"
        }
      ]
    },
    "action_required": "Name mismatch in document 1. Please re-upload the correct document or verify the information."
  }
}
```

## Verification Algorithm

When comparing personal and educational documents:

### Name Comparison
1. Normalize both names (lowercase, remove extra spaces)
2. Check for exact match
3. Check for partial matches (allowing for middle name variations)
4. Score: High (exact match), Medium (partial match), Low (no match)

### DOB Comparison
1. Parse both dates to standard format (DD-MM-YYYY)
2. Compare day, month, year
3. Allow for common OCR errors (e.g., O → 0, l → 1)
4. Score: Match or Mismatch

### Overall Match
- A document is considered **VERIFIED** if:
  - Name match score >= 0.8 (80% similarity)
  - DOB matches exactly
  
- A document is considered **FAILED** if:
  - Either name or DOB doesn't meet the threshold

## Fixing Verification Failures

If verification fails, the user has these options:

1. **Re-upload the correct document** - If they uploaded the wrong document
2. **Update personal information** - If the personal document has incorrect data
3. **Contact support** - If there's a legitimate reason for mismatch (name change, typo in certificate, etc.)

### Re-upload Process
1. Delete or request deletion of incorrect document from database
2. Upload the correct document
3. Call GET `/form/worker/{worker_id}/data` again to re-trigger verification
4. Verification should pass with correct documents

## Implementation Details

### LLM Extraction
Uses OpenAI GPT-4o-mini to extract structured data from OCR text:
- Requires `OPENAI_API_KEY` environment variable
- Sends OCR text with JSON schema prompts
- Returns parsed JSON with extracted fields

### Verification Function
Location: `/services/document_verifier.py`
Function: `verify_documents(personal_name, personal_dob, educational_docs)`

This function:
1. Receives personal extracted name and DOB
2. Compares against each educational document's extracted data
3. Returns detailed comparison results
4. Logs all matches and mismatches

### Database Updates
After verification completes:
1. Updates `workers.verification_status` to 'verified' or 'failed'
2. Updates `workers.verified_at` timestamp
3. Updates `workers.verification_errors` with mismatch details (if failed)
4. Updates each `educational_documents.verification_status` individually
5. Updates `educational_documents.verification_errors` for each failed document

## Troubleshooting

### Issue: Extraction Status Shows "false" for personal_extracted
**Cause**: `personal_extracted_name` or `personal_extracted_dob` is NULL in database

**Solution**: 
1. Check if personal document was uploaded successfully
2. Check if OCR completed (look for background task logs)
3. Check if LLM extraction worked (look for OpenAI API key errors)
4. Re-upload the personal document

### Issue: Verification Skipped
**Cause**: One of the following:
- Personal data hasn't been extracted yet
- No educational documents have been extracted yet
- Both conditions aren't met

**Solution**: 
1. Upload personal document and wait for extraction
2. Upload at least one educational document and wait for extraction
3. Call GET `/form/worker/{worker_id}/data` again

### Issue: False Positive Mismatch
**Cause**: OCR or LLM extracted data incorrectly

**Solution**:
1. Check document quality (blur, poor lighting)
2. Upload a clearer version of the document
3. Verify the extracted data in the response before resubmitting

## Testing Verification

### Test Case 1: Matching Documents
1. Upload personal document with name "John Doe" and DOB "01-01-1990"
2. Upload educational document with same name and DOB
3. Call GET endpoint
4. Expect: verification_status = "verified" (200 response)

### Test Case 2: Mismatched Names
1. Upload personal document with name "John Doe"
2. Upload educational document with name "Jon Doe" (typo)
3. Call GET endpoint
4. Expect: verification_status = "failed" (400 response) with name mismatch

### Test Case 3: Mismatched DOB
1. Upload personal document with DOB "01-01-1990"
2. Upload educational document with DOB "01-01-1991"
3. Call GET endpoint
4. Expect: verification_status = "failed" (400 response) with DOB mismatch
