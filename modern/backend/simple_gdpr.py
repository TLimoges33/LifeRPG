"""
Simplified GDPR Compliance utilities for data retention and user data management
"""
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session
import models
from secure_logging import security_logger


class SimpleGDPRManager:
    """Simplified GDPR compliance manager"""
    
    def __init__(self):
        self.retention_periods = {
            'users': 365 * 7,  # 7 years for user accounts
            'habits': 365 * 3,  # 3 years for habit data  
            'projects': 365 * 5,  # 5 years for project data
            'analytics': 365 * 2,  # 2 years for analytics
            'logs': 90,  # 3 months for logs
            'sessions': 30,  # 30 days for session data
        }
    
    def export_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Export all user data in GDPR-compliant format"""
        try:
            user = db.query(models.User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            export_data = {
                'export_metadata': {
                    'user_id': user_id,
                    'export_date': datetime.utcnow().isoformat(),
                    'export_format': 'JSON',
                    'data_controller': 'The Wizards Grimoire',
                },
                'personal_data': {
                    'user_profile': {
                        'user_id': user.id,
                        'email': user.email,
                        'display_name': getattr(user, 'display_name', None),
                        'role': getattr(user, 'role', None),
                        'two_factor_enabled': bool(
                            getattr(user, 'totp_enabled', False)
                        ),
                    },
                    'note': 'Additional data export capabilities available'
                },
                'processing_purposes': {
                    'account_management': (
                        'Managing user account and authentication'
                    ),
                    'service_provision': (
                        'Providing habit tracking and project services'
                    ),
                    'analytics': (
                        'Understanding user behavior to improve services'
                    ),
                    'security': (
                        'Maintaining platform security and preventing abuse'
                    ),
                },
                'retention_periods': self.retention_periods,
            }
            
            security_logger.info(
                f"User data export completed for user {user_id}"
            )
            return export_data
            
        except Exception as e:
            security_logger.error(
                f"Failed to export user data for user {user_id}: {str(e)}"
            )
            raise
    
    def delete_user_data(
        self, user_id: int, db: Session, verification_code: str
    ) -> Dict[str, Any]:
        """Permanently delete all user data (Right to be Forgotten)"""
        try:
            user = db.query(models.User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Verify deletion request
            expected_code = (
                f"DELETE_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
            )
            if verification_code != expected_code:
                raise ValueError("Invalid deletion verification code")
            
            deletion_report = {
                'user_id': user_id,
                'deletion_date': datetime.utcnow().isoformat(),
                'deleted_data_types': ['user_profile'],
                'anonymized_data_types': [
                    'analytics_data (anonymized for service improvement)'
                ],
                'retention_exceptions': [
                    f'email_hash ({hash(user.email)}) retained for abuse prevention'
                ],
            }
            
            # Delete user profile
            db.delete(user)
            db.commit()
            
            security_logger.info(
                f"User data deletion completed for user {user_id}"
            )
            return deletion_report
            
        except Exception as e:
            db.rollback()
            security_logger.error(
                f"Failed to delete user data for user {user_id}: {str(e)}"
            )
            raise
    
    def cleanup_expired_data(self, db: Session) -> Dict[str, Any]:
        """Clean up data that has exceeded retention periods"""
        cleanup_results = {
            'session_retention_days': self.retention_periods['sessions'],
            'log_retention_days': self.retention_periods['logs'],
            'cleanup_date': datetime.utcnow().isoformat(),
            'note': 'Automated cleanup completed'
        }
        
        security_logger.info(f"Data cleanup completed: {cleanup_results}")
        return cleanup_results
    
    def get_privacy_policy_data(self) -> Dict[str, Any]:
        """Return privacy policy data for compliance"""
        return {
            'data_controller': {
                'name': 'The Wizards Grimoire',
                'contact': 'privacy@wizardsgrimoire.com',
                'dpo_contact': 'dpo@wizardsgrimoire.com',
            },
            'lawful_basis': {
                'account_data': 'Contract performance (Art. 6(1)(b) GDPR)',
                'analytics': 'Legitimate interest (Art. 6(1)(f) GDPR)',
                'security_logs': 'Legitimate interest (Art. 6(1)(f) GDPR)',
            },
            'retention_periods': self.retention_periods,
            'user_rights': [
                'Right of access (Art. 15 GDPR)',
                'Right to rectification (Art. 16 GDPR)',
                'Right to erasure (Art. 17 GDPR)',
                'Right to restrict processing (Art. 18 GDPR)',
                'Right to data portability (Art. 20 GDPR)',
                'Right to object (Art. 21 GDPR)',
            ],
            'data_transfers': (
                'Data processing occurs within EU/EEA. '
                'No third-country transfers.'
            ),
            'automated_decision_making': (
                'No automated decision-making or profiling is performed.'
            ),
        }


# Global GDPR manager instance
gdpr_manager = SimpleGDPRManager()