@router.post("/{worker_id}/document-reupload")
async def handle_document_reupload(worker_id: str, request: dict):
    """
    Handle document re-upload after verification mismatch.
    
    When personal and educational documents don't match (name/dob mismatch),
    user can choose which document to re-upload:
    - "educational_only": Clear only educational data, keep personal
    - "personal_and_educational": Clear all data (full reset)
    
    Args:
        worker_id: Worker ID
        request: {"action": "educational_only" | "personal_and_educational"}
        
    Returns:
        Success/failure response
    """
    try:
        logger.info(f"[REUPLOAD] Received re-upload request for worker {worker_id}")
        
        # Validate worker exists
        worker = crud.get_worker(worker_id)
        if not worker:
            logger.error(f"[REUPLOAD] Worker {worker_id} not found")
            raise HTTPException(status_code=404, detail="Worker not found")
        
        # Extract action from request
        action = request.get("action", "").lower()
        logger.info(f"[REUPLOAD] Action requested: {action}")
        
        if action == "educational_only":
            logger.info(f"[REUPLOAD] Clearing educational documents for {worker_id}...")
            success = crud.clear_educational_documents_for_reupload(worker_id)
            
            if success:
                logger.info(f"[REUPLOAD] ✓ Educational documents cleared. User can now re-upload educational document.")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "action": "educational_only",
                        "message": "Educational document data cleared. Please re-upload the correct educational document.",
                        "worker_id": worker_id,
                        "cleared_data": {
                            "educational": True,
                            "personal": False
                        }
                    }
                )
            else:
                logger.error(f"[REUPLOAD] Failed to clear educational documents for {worker_id}")
                raise HTTPException(status_code=500, detail="Failed to clear educational document data")
        
        elif action == "personal_and_educational":
            logger.info(f"[REUPLOAD] Clearing ALL documents for {worker_id}...")
            success = crud.clear_all_documents_for_reupload(worker_id)
            
            if success:
                logger.info(f"[REUPLOAD] ✓ All documents cleared. User starts fresh workflow.")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "action": "personal_and_educational",
                        "message": "All document data cleared. Please start over by uploading your personal document first.",
                        "worker_id": worker_id,
                        "cleared_data": {
                            "educational": True,
                            "personal": True,
                            "experience": True,
                            "voice_sessions": True
                        }
                    }
                )
            else:
                logger.error(f"[REUPLOAD] Failed to clear all documents for {worker_id}")
                raise HTTPException(status_code=500, detail="Failed to clear all document data")
        
        else:
            logger.error(f"[REUPLOAD] Invalid action: {action}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Must be 'educational_only' or 'personal_and_educational'. Got: {action}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REUPLOAD] Error handling re-upload for {worker_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error handling re-upload: {str(e)}")
