# Quick Reference Card - Document Re-upload Implementation

## What Changed

| Component | Change | Status |
|-----------|--------|--------|
| db/crud.py | +2 new functions for cleanup | ✓ Added |
| api/form.py | +1 new endpoint for re-upload | ✓ Added |
| api/form.py | Updated verification error response | ✓ Modified |
| Database | No schema changes needed | ✓ Compatible |
| APIs | New POST endpoint added | ✓ Non-breaking |

---

## New Functions

### 1. clear_educational_documents_for_reupload()
```python
# Signature
def clear_educational_documents_for_reupload(worker_id: str) -> bool

# What it does
- Deletes educational_documents row
- Keeps personal document data
- Resets education flags in workers table

# Returns
- True if successful
- False if error

# Usage
success = crud.clear_educational_documents_for_reupload(worker_id)
```

### 2. clear_all_documents_for_reupload()
```python
# Signature
def clear_all_documents_for_reupload(worker_id: str) -> bool

# What it does
- Deletes personal_documents row
- Deletes educational_documents row
- Deletes work_experience rows
- Deletes voice_sessions rows
- Resets all worker fields to NULL/0

# Returns
- True if successful
- False if error

# Usage
success = crud.clear_all_documents_for_reupload(worker_id)
```

---

## New API Endpoint

### POST /form/{worker_id}/document-reupload

```
Method: POST
Path: /form/{worker_id}/document-reupload
Content-Type: application/json

Request Body:
{
  "action": "educational_only" | "personal_and_educational"
}

Success Response (200):
{
  "status": "success",
  "action": "string",
  "message": "string",
  "worker_id": "string",
  "cleared_data": {
    "educational": boolean,
    "personal": boolean,
    "experience": boolean,
    "voice_sessions": boolean
  }
}

Error Response (400/404/500):
{
  "detail": "error message"
}
```

---

## Frontend Flow

```javascript
// 1. Check verification response
if (response.status === 400 && data.responseData.reupload_options) {
  
  // 2. Show dialog with options
  showDialog(data.responseData.reupload_options);
  
  // 3. User picks option
  if (userChoice === 'educational_only') {
    // 4a. Clear educational only
    POST /form/{worker_id}/document-reupload
    {"action": "educational_only"}
    // → User uploads new educational document
    
  } else if (userChoice === 'personal_and_educational') {
    // 4b. Clear everything
    POST /form/{worker_id}/document-reupload
    {"action": "personal_and_educational"}
    // → User starts fresh workflow
  }
}
```

---

## Decision Tree

```
Verification Fails (Name/DOB Mismatch)
         ↓
Show Dialog:
"Which document to re-upload?"
         ├─ Educational Only?
         │  └─ Keep personal, fix educational only
         │     └─ POST with action="educational_only"
         │
         └─ Fresh Start?
            └─ Clear everything, start over
               └─ POST with action="personal_and_educational"
```

---

## Database Operations

### If "educational_only":
```sql
DELETE FROM educational_documents WHERE worker_id = ?;
UPDATE workers SET education = NULL, has_education = 0, 
                  education_verified = 0 WHERE worker_id = ?;
```

### If "personal_and_educational":
```sql
DELETE FROM personal_documents WHERE worker_id = ?;
DELETE FROM educational_documents WHERE worker_id = ?;
DELETE FROM work_experience WHERE worker_id = ?;
DELETE FROM voice_sessions WHERE worker_id = ?;
UPDATE workers SET 
  personal_extracted_name = NULL,
  personal_extracted_dob = NULL,
  name = NULL, dob = NULL,
  gender = NULL, address = NULL, email = NULL,
  education = NULL, has_education = 0,
  education_verified = 0, personal_verified = 0,
  has_cv = 0, ocr_status = 'pending'
WHERE worker_id = ?;
```

---

## Implementation Checklist

### Backend
- [x] Added cleanup functions to crud.py
- [x] Added re-upload endpoint to form.py
- [x] Updated verification error response
- [x] Added comprehensive logging
- [x] Added error handling
- [x] Tested for backward compatibility

### Frontend
- [ ] Check for reupload_options in verification failure response
- [ ] Show re-upload dialog with 2 options
- [ ] Implement POST call to re-upload endpoint
- [ ] Handle success/error responses
- [ ] Redirect to appropriate upload screen
- [ ] Allow fresh document upload process

---

## Testing Commands

### Test Educational Only Re-upload
```bash
# After verification fails
curl -X POST http://localhost:8000/api/form/{worker_id}/document-reupload \
  -H "Content-Type: application/json" \
  -d '{"action": "educational_only"}'

# Expected: Educational data cleared, personal data preserved
```

### Test Complete Reset
```bash
curl -X POST http://localhost:8000/api/form/{worker_id}/document-reupload \
  -H "Content-Type: application/json" \
  -d '{"action": "personal_and_educational"}'

# Expected: All data cleared, worker reset to initial state
```

---

## Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| db/crud.py | 1329-1464 | Cleanup functions |
| api/form.py | 2456-2547 | Re-upload endpoint |
| api/form.py | 722-750 | Updated error response |

---

## Logging Prefix

All re-upload operations logged with: **[REUPLOAD]**

Examples:
```
[REUPLOAD] Clearing educational documents for worker_id...
[REUPLOAD] ✓ Educational documents cleared. Ready for re-upload.
[REUPLOAD] Performing FULL DATA CLEAR for worker_id...
[REUPLOAD] ✓ ALL documents cleared. Complete reset ready.
[REUPLOAD] Error handling re-upload...
```

---

## Key Points

✓ **No data corruption** - Uses DELETE (clean removal)
✓ **No breaking changes** - Fully backward compatible
✓ **User control** - Two clear options to choose from
✓ **Fresh processing** - All old data is gone before new upload
✓ **Safe retry** - Users can retry multiple times
✓ **Well logged** - All operations tracked with [REUPLOAD] prefix
✓ **Production ready** - Tested and documented

---

## What Stays the Same

- OCR extraction process
- LLM extraction process
- Verification algorithm
- Document upload endpoints
- Background processing
- Voice call integration
- Worker data management
- All other APIs and endpoints

**ONLY ADDS recovery capability for verification failures.**

---

## Common Scenarios

### Scenario 1: Wrong Educational Document
```
User realizes: Educational document had typo in name
Solution: Choose "Re-upload Educational Only"
Result: Personal data kept, educational data cleared, user uploads correct document
```

### Scenario 2: Both Documents Wrong
```
User realizes: Both documents are incorrect
Solution: Choose "Fresh Start (Re-upload All)"
Result: All data cleared, user starts fresh workflow from beginning
```

### Scenario 3: Multiple Re-uploads
```
User tries: Educational only → verification still fails
Solution: Show re-upload options again
Result: User can choose same option again or switch to fresh start
```

---

## Response Headers

### Verification Failed (Before Changes)
```
Status: 400
{
  "status": "verification_failed",
  "message": "...",
  "verification": {...}
}
```

### Verification Failed (After Changes)
```
Status: 400
{
  "status": "verification_failed",
  "message": "...",
  "verification": {...},
  "reupload_options": {
    "options": [
      {"action": "educational_only", ...},
      {"action": "personal_and_educational", ...}
    ]
  }
}
```

---

## Summary

**In 3 sentences:**
When document verification fails due to name/DOB mismatch, the system now provides users with two clear recovery options: (1) Re-upload only the educational document if personal is correct, or (2) Start completely fresh with both documents. The selected option clears the appropriate data from the database and allows the user to retry with fresh OCR and LLM processing.
