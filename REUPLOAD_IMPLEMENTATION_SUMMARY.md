# Re-upload Implementation - Changes Summary

## Files Modified

### 1. `/vercel/share/v0-project/db/crud.py`
**Added 2 new cleanup functions:**

- `clear_educational_documents_for_reupload(worker_id)` - Lines 1329-1364
  - Clears only educational document data
  - Keeps personal document data intact
  - Resets education verification flags
  - Use case: User re-uploads educational document only

- `clear_all_documents_for_reupload(worker_id)` - Lines 1367-1464
  - Clears ALL documents, experience, and voice sessions
  - Resets worker to initial state
  - Preserves worker ID and mobile number
  - Use case: User starts fresh with personal document

**Status:** ✓ Added successfully (136 lines)

---

### 2. `/vercel/share/v0-project/api/form.py`
**Modified: 2 sections**

**A. Added new endpoint:** `handle_document_reupload()` - Lines 2456-2547
- POST /form/{worker_id}/document-reupload
- Accepts action: "educational_only" or "personal_and_educational"
- Calls appropriate cleanup function
- Returns success/failure response

**B. Updated verification failed response:** Lines 722-750
- When verification fails (400 response)
- Now includes `reupload_options` object with 2 clear options
- Shows endpoint URL for frontend to call
- Provides detailed descriptions and next steps

**Status:** ✓ Added successfully (93 lines)

---

### 3. `/vercel/share/v0-project/api/form_reupload_endpoint.py`
**Created new file with reupload endpoint** (91 lines)
- Standalone version of the endpoint (kept for reference)
- Also added to form.py (above is the actual implementation)

---

## Features Implemented

### ✓ Feature 1: Educational Document Only Re-upload
When verification fails but personal document is correct:
- User selects: "Re-upload Educational Document Only"
- System clears: Only educational_documents row
- System preserves: Personal document data
- Flow: User uploads new educational document → Fresh OCR → Fresh LLM → Verification again
- Result: If matches now → Proceed; If still mismatches → Show re-upload option again

### ✓ Feature 2: Complete Re-upload (Fresh Start)
When user wants to start completely over:
- User selects: "Re-upload All Documents (Fresh Start)"
- System clears: Everything (personal, educational, experience, voice)
- System resets: Worker to initial state
- Flow: Same as first-time signup
- Result: User uploads personal → educational → verification → proceed

### ✓ Feature 3: Re-upload Options in Response
When verification fails:
- GET /worker/{worker_id}/data returns 400 status
- Includes `reupload_options` object with:
  - Clear description of each option
  - API endpoint to call for each option
  - Next steps explanation
  - User can make informed choice

---

## Database Changes

### No Schema Changes Required
- Uses existing tables and columns
- No new columns added
- Uses DELETE operations (safe and complete)
- Preserves referential integrity

### Operations Performed:
```sql
-- Educational Only
DELETE FROM educational_documents WHERE worker_id = ?
UPDATE workers SET education = NULL, has_education = 0, education_verified = 0 WHERE worker_id = ?

-- Complete Reset
DELETE FROM personal_documents WHERE worker_id = ?
DELETE FROM educational_documents WHERE worker_id = ?
DELETE FROM work_experience WHERE worker_id = ?
DELETE FROM voice_sessions WHERE worker_id = ?
UPDATE workers SET [all fields reset to NULL/0] WHERE worker_id = ?
```

---

## API Changes

### New Endpoint
```
POST /form/{worker_id}/document-reupload
Content-Type: application/json

Body:
{
  "action": "educational_only" | "personal_and_educational"
}

Response:
{
  "status": "success",
  "action": "educational_only" | "personal_and_educational",
  "message": "...",
  "worker_id": "...",
  "cleared_data": { ... }
}
```

### Updated Endpoint
```
GET /worker/{worker_id}/data

When verification_status = "failed":
Returns 400 with:
- verification_errors (same as before)
- NEW: reupload_options object with 2 options
```

---

## Backward Compatibility

✓ **100% Backward Compatible**
- No breaking changes to existing APIs
- No schema migrations needed
- No changes to OCR/LLM extraction
- No changes to verification algorithm
- All existing endpoints work exactly as before
- Only ADDS functionality when verification fails

---

## Error Handling

- Invalid action name → 400 with clear error message
- Worker not found → 404
- Database errors → 500 with error message
- All errors logged with [REUPLOAD] prefix for debugging

---

## Logging

All operations logged with `[REUPLOAD]` prefix:
```
[REUPLOAD] Clearing educational documents for worker_id_here...
[REUPLOAD] Deleted 1 educational document row(s)
[REUPLOAD] ✓ Educational documents cleared for worker_id_here. Ready for re-upload.

[REUPLOAD] Performing FULL DATA CLEAR for worker_id_here...
[REUPLOAD] Deleted 1 personal document row(s)
[REUPLOAD] Deleted 1 educational document row(s)
[REUPLOAD] ✓ ALL documents and experience cleared for worker_id_here. Complete reset ready for new uploads.
```

---

## Testing Scenarios

### Scenario 1: Educational Only Re-upload
1. Upload personal: "BABU KHAN", DOB: "15-05-1995"
2. Upload educational: "WRONG NAME", DOB: "20-06-2000"
3. Verification fails
4. User clicks: "Re-upload Educational Document Only"
5. POST /form/{worker_id}/document-reupload with action="educational_only"
6. Educational data cleared
7. User uploads new educational: "BABU KHAN", DOB: "15-05-1995"
8. Verification passes
9. Proceed to next step

### Scenario 2: Complete Fresh Start
1. Upload personal: "BABU KHAN", DOB: "15-05-1995"
2. Upload educational: "WRONG NAME", DOB: "20-06-2000"
3. Verification fails
4. User clicks: "Re-upload All Documents"
5. POST /form/{worker_id}/document-reupload with action="personal_and_educational"
6. All data cleared, worker reset to initial state
7. Same workflow as first-time user starts

---

## Files Created

1. `/vercel/share/v0-project/REUPLOAD_IMPLEMENTATION_GUIDE.md` - Complete user flow guide
2. `/vercel/share/v0-project/api/form_reupload_endpoint.py` - Standalone endpoint (reference)
3. `/vercel/share/v0-project/REUPLOAD_IMPLEMENTATION_SUMMARY.md` - This file

---

## Deployment Notes

✓ Ready to deploy immediately
✓ No database migrations needed
✓ No environment variables needed
✓ No config changes needed
✓ Fully backward compatible
✓ All logging in place for debugging

---

## Summary

The re-upload implementation adds the ability for users to recover from document verification mismatches. When personal and educational documents don't match (name/dob mismatch), users can:

1. **Re-upload Educational Only** - Keep personal, upload corrected educational document
2. **Fresh Start** - Clear everything and start the workflow again

All changes are backward compatible, well-logged, and maintain data integrity. Original functionality is completely preserved.
