# Frontend Integration Guide - Document Re-upload

## Overview
This guide explains how the frontend should integrate with the new re-upload functionality when document verification fails.

---

## Current Flow (Before Changes)
```
Upload Personal & Educational
    ↓
Background OCR + LLM
    ↓
Verification Check
    ├─ Match: Show "Verified" (old data stays)
    └─ Mismatch: Show Error (old data stays - PROBLEM)
```

## New Flow (With Re-upload Implementation)
```
Upload Personal & Educational
    ↓
Background OCR + LLM
    ↓
Verification Check
    ├─ Match: Proceed to next step ✓
    └─ Mismatch: Show Dialog with Re-upload Options
         ├─ Option A: "Re-upload Educational Only"
         │    └─ Call: POST /form/{worker_id}/document-reupload
         │         Body: {"action": "educational_only"}
         │         Result: Clear educational data, allow fresh upload
         │
         └─ Option B: "Fresh Start (Re-upload All)"
              └─ Call: POST /form/{worker_id}/document-reupload
                   Body: {"action": "personal_and_educational"}
                   Result: Clear all data, start workflow from beginning
```

---

## Step-by-Step Frontend Implementation

### Step 1: Detect Verification Failure
Currently you're checking GET /worker/{worker_id}/data response.

```javascript
// When verification fails:
const response = await fetch(`/api/worker/${workerId}/data`);

if (response.status === 400) {
  const data = await response.json();
  
  if (data.responseData.status === 'verification_failed') {
    // NEW: Check for reupload_options
    if (data.responseData.reupload_options) {
      showReuploadDialog(workerId, data.responseData);
    }
  }
}
```

### Step 2: Show Re-upload Dialog
Display the two options clearly to the user:

```javascript
function showReuploadDialog(workerId, verificationData) {
  const options = verificationData.reupload_options.options;
  
  // Option A: Educational Only
  const educationalOnlyOption = options.find(o => o.action === 'educational_only');
  
  // Option B: Personal + Educational
  const fullResetOption = options.find(o => o.action === 'personal_and_educational');
  
  // Display dialog with both options
  showDialog({
    title: "Document Verification Failed",
    message: verificationData.verification.mismatches.map(m => 
      `${m.type}: Personal has "${m.personal}" but Educational has "${m.educational}"`
    ).join('\n'),
    
    primaryButton: {
      label: educationalOnlyOption.label,
      description: educationalOnlyOption.description,
      onClick: () => handleReupload(workerId, 'educational_only')
    },
    
    secondaryButton: {
      label: fullResetOption.label,
      description: fullResetOption.description,
      onClick: () => handleReupload(workerId, 'personal_and_educational')
    }
  });
}
```

### Step 3: Handle Re-upload Selection
When user clicks on one of the options:

```javascript
async function handleReupload(workerId, action) {
  try {
    // Step 1: Call re-upload endpoint to clear data
    const clearResponse = await fetch(
      `/api/form/${workerId}/document-reupload`,
      {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action})
      }
    );
    
    if (!clearResponse.ok) {
      showError('Failed to clear document data. Please try again.');
      return;
    }
    
    const clearData = await clearResponse.json();
    
    // Step 2: Show confirmation message
    showSuccess(clearData.message);
    
    // Step 3: Redirect to appropriate upload screen
    if (action === 'educational_only') {
      // Show educational document upload screen
      // Personal data is preserved, user uploads new educational document
      redirectTo('/upload/educational');
    } else if (action === 'personal_and_educational') {
      // Reset workflow - start from personal document upload
      // All data is cleared, user starts fresh
      redirectTo('/upload/personal');
    }
  } catch (error) {
    showError('Error handling re-upload: ' + error.message);
  }
}
```

### Step 4: Handle Fresh Upload After Clearing
After data is cleared, user can upload new document(s):

```javascript
// For "educational_only" re-upload:
async function uploadEducationalAfterReupload(workerId, file) {
  // Same as normal educational upload
  // Call: POST /form/educational-document
  // But this time it will:
  //   1. Process with fresh OCR (old data is gone)
  //   2. Extract with fresh LLM (no old data in DB)
  //   3. Run verification again
  //   4. If matches now: proceed; if not: show re-upload option again
}

// For "personal_and_educational" re-upload:
async function uploadPersonalAfterReset(workerId, file) {
  // Same as initial personal upload
  // But worker is in "reset" state
  // After personal upload: ask for educational
  // Run verification again from scratch
}
```

---

## Response Handling Examples

### Verification Failed Response (Status 400)
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
          "type": "name_mismatch",
          "personal": "BABU KHAN",
          "educational": "DIFFERENT NAME",
          "similarity": 0.45
        },
        {
          "type": "dob_mismatch",
          "personal": "15-05-1995",
          "educational": "20-06-2000"
        }
      ]
    },
    "action_required": "Name mismatch and DOB mismatch detected...",
    "reupload_options": {
      "description": "Choose which document to re-upload after fixing the issue",
      "options": [
        {
          "action": "educational_only",
          "label": "Re-upload Educational Document Only",
          "description": "Keep personal document, upload a new educational document with correct name/DOB",
          "endpoint": "/form/{worker_id}/document-reupload",
          "next_step": "You will be able to upload a new educational document"
        },
        {
          "action": "personal_and_educational",
          "label": "Re-upload All Documents (Fresh Start)",
          "description": "Start over with both personal and educational documents",
          "endpoint": "/form/{worker_id}/document-reupload",
          "next_step": "Start the workflow from the beginning by uploading personal document first"
        }
      ]
    }
  }
}
```

### Re-upload Clear Response (Status 200)
```json
{
  "status": "success",
  "action": "educational_only",
  "message": "Educational document data cleared. Please re-upload the correct educational document.",
  "worker_id": "8dad5957-59ad-4c71-b737-d61886d39bb5",
  "cleared_data": {
    "educational": true,
    "personal": false
  }
}
```

Or:
```json
{
  "status": "success",
  "action": "personal_and_educational",
  "message": "All document data cleared. Please start over by uploading your personal document first.",
  "worker_id": "8dad5957-59ad-4c71-b737-d61886d39bb5",
  "cleared_data": {
    "educational": true,
    "personal": true,
    "experience": true,
    "voice_sessions": true
  }
}
```

---

## UI/UX Recommendations

### Dialog Design
```
┌─────────────────────────────────────────┐
│ Documents Don't Match                   │
├─────────────────────────────────────────┤
│ Name Mismatch:                          │
│ Personal: "BABU KHAN"                   │
│ Educational: "DIFFERENT NAME"           │
│                                         │
│ DOB Mismatch:                           │
│ Personal: "15-05-1995"                  │
│ Educational: "20-06-2000"               │
│                                         │
│ What would you like to do?              │
│                                         │
│ [Option A Button]                       │
│ Re-upload Educational Only              │
│ Keep personal doc, fix educational doc  │
│                                         │
│ [Option B Button]                       │
│ Fresh Start                             │
│ Start over with both documents          │
│                                         │
│ [Cancel]                                │
└─────────────────────────────────────────┘
```

### Flow Diagram
```
User Sees Verification Failed
         ↓
Shows Dialog with 2 Options
         ├─ Option A: "Fix Educational Only"
         │    ↓
         │    POST /form/.../document-reupload
         │    (action: "educational_only")
         │    ↓
         │    Show Educational Upload Screen
         │    ↓
         │    User Uploads Corrected Document
         │    ↓
         │    Fresh OCR + LLM + Verification
         │
         └─ Option B: "Fresh Start"
              ↓
              POST /form/.../document-reupload
              (action: "personal_and_educational")
              ↓
              Show Personal Upload Screen
              ↓
              User Starts Fresh Workflow
```

---

## Code Template

```javascript
// Frontend handler for verification failure
function handleVerificationFailure(workerId, verificationData) {
  const mismatches = verificationData.verification.mismatches;
  
  // Build mismatch message
  const mismatchMessage = mismatches
    .map(m => `${m.type}: "${m.personal}" vs "${m.educational}"`)
    .join('\n');
  
  // Show dialog with re-upload options
  showDialog({
    type: 'warning',
    title: 'Document Verification Failed',
    description: `The information in your documents don't match:\n\n${mismatchMessage}`,
    buttons: [
      {
        text: 'Re-upload Educational Only',
        variant: 'primary',
        onClick: async () => {
          await clearAndReupload(workerId, 'educational_only');
          navigateTo('/upload/educational');
        }
      },
      {
        text: 'Fresh Start (Re-upload All)',
        variant: 'secondary',
        onClick: async () => {
          await clearAndReupload(workerId, 'personal_and_educational');
          navigateTo('/upload/personal');
        }
      },
      {
        text: 'Cancel',
        variant: 'ghost'
      }
    ]
  });
}

// Helper function to clear data via API
async function clearAndReupload(workerId, action) {
  const response = await fetch(`/api/form/${workerId}/document-reupload`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action})
  });
  
  if (!response.ok) {
    throw new Error('Failed to clear documents');
  }
  
  return response.json();
}
```

---

## Notes

- Keep re-upload options simple and clear
- Show which documents will be affected in each option
- After re-upload, old data is completely gone (fresh processing)
- If verification still fails after re-upload, options appear again
- User can retry multiple times without issues
- No data corruption or stuck states possible

---

## Testing Checklist for Frontend

- [ ] Verification fails → Dialog shows up with options
- [ ] Click "Educational Only" → POST request sent correctly
- [ ] Response received → Message shows "Educational data cleared"
- [ ] Redirect to educational upload screen works
- [ ] User can upload new educational document
- [ ] Verification runs again on new upload
- [ ] Click "Fresh Start" → POST request sent correctly
- [ ] All data cleared (personal + educational)
- [ ] Redirect to personal upload screen works
- [ ] Complete fresh workflow possible
- [ ] Error messages clear if something fails
- [ ] Cancel button works (dialog closes)

