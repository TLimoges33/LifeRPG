"""
GDPR API endpoints for user data management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from auth import get_current_user
from db import get_db
from simple_gdpr import gdpr_manager
from secure_logging import security_logger
import models

router = APIRouter(prefix="/api/gdpr", tags=["GDPR"])


@router.get("/export-data")
async def export_user_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export all user data in GDPR-compliant format
    
    Returns comprehensive export of all personal data associated with user
    """
    try:
        export_data = gdpr_manager.export_user_data(
            current_user.id, db
        )
        
        security_logger.info(
            f"GDPR data export requested by user {current_user.id}",
            extra={"user_id": current_user.id, "action": "data_export"}
        )
        
        return export_data
        
    except Exception as e:
        security_logger.error(
            f"GDPR data export failed for user {current_user.id}: {str(e)}",
            extra={"user_id": current_user.id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )


@router.delete("/delete-account")
async def delete_user_account(
    verification_code: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Permanently delete user account and all associated data
    
    Requires verification code for security
    """
    try:
        deletion_report = gdpr_manager.delete_user_data(
            current_user.id, db, verification_code
        )
        
        security_logger.warning(
            f"User account deletion completed for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "action": "account_deletion",
                "deletion_date": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "message": "Account successfully deleted",
            "deletion_report": deletion_report
        }
        
    except ValueError as e:
        security_logger.warning(
            f"Invalid deletion request for user {current_user.id}: {str(e)}",
            extra={"user_id": current_user.id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        security_logger.error(
            f"Account deletion failed for user {current_user.id}: {str(e)}",
            extra={"user_id": current_user.id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/privacy-policy")
async def get_privacy_policy() -> Dict[str, Any]:
    """
    Get privacy policy information including data processing details
    """
    return gdpr_manager.get_privacy_policy_data()


@router.get("/retention-policy")
async def get_retention_policy(
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data retention policy information
    """
    return {
        "retention_periods": gdpr_manager.retention_periods,
        "policy_effective_date": "2024-01-01",
        "policy_version": "1.0",
        "automatic_cleanup": True,
        "user_rights": [
            "Request data export at any time",
            "Request account deletion at any time",
            "Update personal information",
            "Withdraw consent for non-essential processing"
        ]
    }


@router.post("/generate-deletion-code")
async def generate_deletion_code(
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Generate verification code for account deletion
    
    In production, this would send the code via email
    """
    deletion_code = (
        f"DELETE_{current_user.id}_"
        f"{datetime.utcnow().strftime('%Y%m%d')}"
    )
    
    security_logger.info(
        f"Deletion verification code generated for user {current_user.id}",
        extra={"user_id": current_user.id, "action": "deletion_code_generated"}
    )
    
    # In production, send this via secure email
    return {
        "message": "Deletion code generated",
        "code": deletion_code,  # Only for demo - remove in production
        "note": "In production, this code would be sent via email"
    }
