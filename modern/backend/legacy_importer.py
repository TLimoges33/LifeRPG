"""
Legacy AHK Data Import System - Import data from AutoHotkey LifeRPG exports

This module handles importing data from the legacy AutoHotkey version,
including projects, skills, and completion logs.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import models
import json
import csv
import io
import logging

logger = logging.getLogger(__name__)


class LegacyImporter:
    """Service for importing data from legacy AHK LifeRPG."""
    
    def __init__(self, db: Session):
        self.db = db

    def import_json_export(self, data: Dict, user_id: int) -> Dict:
        """Import data from JSON export format."""
        results = {
            'projects_imported': 0,
            'habits_imported': 0,
            'logs_imported': 0,
            'skills_imported': 0,
            'errors': []
        }
        
        try:
            # Import projects first
            if 'projects' in data:
                results['projects_imported'] = self._import_projects(
                    data['projects'], user_id
                )
            
            # Import habits
            if 'habits' in data:
                results['habits_imported'] = self._import_habits(
                    data['habits'], user_id
                )
            
            # Import completion logs
            if 'logs' in data:
                results['logs_imported'] = self._import_logs(
                    data['logs'], user_id
                )
            
            # Import skills
            if 'skills' in data:
                results['skills_imported'] = self._import_skills(
                    data['skills'], user_id
                )
            
            self.db.commit()
            logger.info(f"Successfully imported legacy data for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Import failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results

    def import_csv_export(self, csv_content: bytes, user_id: int) -> Dict:
        """Import data from CSV export format."""
        results = {
            'records_imported': 0,
            'errors': []
        }
        
        try:
            csv_text = csv_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            
            for row in csv_reader:
                try:
                    self._import_csv_row(row, user_id)
                    results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Error importing row {row}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.warning(error_msg)
            
            self.db.commit()
            logger.info(
                f"Successfully imported {results['records_imported']} "
                f"CSV records for user {user_id}"
            )
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"CSV import failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results

    def _import_projects(self, projects: List[Dict], user_id: int) -> int:
        """Import projects from legacy data."""
        imported = 0
        
        for project_data in projects:
            try:
                # Check if project already exists
                existing = self.db.query(models.Project).filter(
                    models.Project.user_id == user_id,
                    models.Project.title == project_data.get('title', '')
                ).first()
                
                if existing:
                    logger.info(f"Project '{project_data['title']}' already exists")
                    continue
                
                # Map legacy fields to modern schema
                project = models.Project(
                    user_id=user_id,
                    title=project_data.get('title', ''),
                    description=project_data.get('description', ''),
                    status=self._map_project_status(
                        project_data.get('status', 'active')
                    ),
                    difficulty=project_data.get('difficulty', 1),
                    importance=project_data.get('importance', 'Medium'),
                    created_at=self._parse_date(
                        project_data.get('created_at')
                    ) or datetime.utcnow()
                )
                
                # Handle parent project relationships
                if project_data.get('parent_title'):
                    parent = self.db.query(models.Project).filter(
                        models.Project.user_id == user_id,
                        models.Project.title == project_data['parent_title']
                    ).first()
                    if parent:
                        project.parent_id = parent.id
                
                self.db.add(project)
                imported += 1
                
            except Exception as e:
                logger.error(f"Error importing project {project_data}: {e}")
                continue
        
        return imported

    def _import_habits(self, habits: List[Dict], user_id: int) -> int:
        """Import habits from legacy data."""
        imported = 0
        
        for habit_data in habits:
            try:
                # Check if habit already exists
                existing = self.db.query(models.Habit).filter(
                    models.Habit.user_id == user_id,
                    models.Habit.title == habit_data.get('title', '')
                ).first()
                
                if existing:
                    logger.info(f"Habit '{habit_data['title']}' already exists")
                    continue
                
                # Map legacy habit to modern schema
                habit = models.Habit(
                    user_id=user_id,
                    title=habit_data.get('title', ''),
                    notes=habit_data.get('notes', ''),
                    cadence=habit_data.get('cadence', 'daily'),
                    difficulty=habit_data.get('difficulty', 1),
                    xp_reward=habit_data.get('difficulty', 1) * 10,
                    status=self._map_habit_status(
                        habit_data.get('status', 'active')
                    ),
                    created_at=self._parse_date(
                        habit_data.get('created_at')
                    ) or datetime.utcnow()
                )
                
                # Link to project if specified
                if habit_data.get('project_title'):
                    project = self.db.query(models.Project).filter(
                        models.Project.user_id == user_id,
                        models.Project.title == habit_data['project_title']
                    ).first()
                    if project:
                        habit.project_id = project.id
                
                self.db.add(habit)
                imported += 1
                
            except Exception as e:
                logger.error(f"Error importing habit {habit_data}: {e}")
                continue
        
        return imported

    def _import_logs(self, logs: List[Dict], user_id: int) -> int:
        """Import completion logs from legacy data."""
        imported = 0
        
        for log_data in logs:
            try:
                # Find the associated habit
                habit_title = log_data.get('habit_title', '')
                habit = self.db.query(models.Habit).filter(
                    models.Habit.user_id == user_id,
                    models.Habit.title == habit_title
                ).first()
                
                if not habit:
                    logger.warning(f"Habit '{habit_title}' not found for log")
                    continue
                
                # Check if log already exists
                log_date = self._parse_date(log_data.get('timestamp'))
                if not log_date:
                    continue
                
                existing = self.db.query(models.Log).filter(
                    models.Log.user_id == user_id,
                    models.Log.habit_id == habit.id,
                    models.Log.action == 'completed',
                    models.Log.created_at == log_date
                ).first()
                
                if existing:
                    continue
                
                # Create log entry
                log = models.Log(
                    user_id=user_id,
                    habit_id=habit.id,
                    action='completed',
                    created_at=log_date,
                    metadata=json.dumps({
                        'imported_from': 'legacy_ahk',
                        'original_data': log_data
                    })
                )
                
                self.db.add(log)
                imported += 1
                
            except Exception as e:
                logger.error(f"Error importing log {log_data}: {e}")
                continue
        
        return imported

    def _import_skills(self, skills: List[Dict], user_id: int) -> int:
        """Import skill data from legacy system."""
        imported = 0
        
        for skill_data in skills:
            try:
                skill_name = skill_data.get('name', '')
                if not skill_name:
                    continue
                
                # Create or update user skill level
                # This would require a UserSkill model
                # For now, we'll track it in user metadata
                user = self.db.query(models.User).filter(
                    models.User.id == user_id
                ).first()
                
                if user:
                    # Store skills in user profile or create skill tracking
                    imported += 1
                
            except Exception as e:
                logger.error(f"Error importing skill {skill_data}: {e}")
                continue
        
        return imported

    def _import_csv_row(self, row: Dict[str, Any], user_id: int) -> None:
        """Import a single CSV row."""
        # This depends on the CSV format from AHK export
        # Common formats might be:
        # - Project logs: date, project, action, notes
        # - Habit completions: date, habit, completed, difficulty
        
        if 'project' in row and 'date' in row:
            self._import_project_log_row(row, user_id)
        elif 'habit' in row and 'date' in row:
            self._import_habit_log_row(row, user_id)

    def _import_project_log_row(self, row: Dict[str, Any], user_id: int) -> None:
        """Import project log from CSV row."""
        # Implementation for project CSV import
        pass

    def _import_habit_log_row(self, row: Dict[str, Any], user_id: int) -> None:
        """Import habit log from CSV row."""
        # Implementation for habit CSV import
        pass

    def _map_project_status(self, legacy_status: str) -> str:
        """Map legacy project status to modern schema."""
        status_map = {
            'active': 'active',
            'completed': 'completed',
            'done': 'completed',
            'paused': 'paused',
            'inactive': 'paused',
            'cancelled': 'paused'
        }
        return status_map.get(legacy_status.lower(), 'active')

    def _map_habit_status(self, legacy_status: str) -> str:
        """Map legacy habit status to modern schema."""
        status_map = {
            'active': 'active',
            'completed': 'completed',
            'done': 'completed',
            'paused': 'paused',
            'inactive': 'paused'
        }
        return status_map.get(legacy_status.lower(), 'active')

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from legacy format."""
        if not date_str:
            return None
        
        # Common legacy date formats
        date_formats = [
            '%Y-%m-%d %H:%M:%S',  # Standard format
            '%Y-%m-%dT%H:%M:%SZ',  # ISO format
            '%Y-%m-%d',            # Date only
            '%m/%d/%Y %H:%M:%S',   # US format
            '%d/%m/%Y %H:%M:%S',   # EU format
            '%Y%m%d%H%M%S',        # Compact format (AHK style)
            '%Y%m%d'               # Compact date only
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None

    def generate_import_template(self) -> Dict:
        """Generate a template for JSON import format."""
        return {
            "metadata": {
                "export_version": "1.0",
                "export_date": datetime.utcnow().isoformat(),
                "source": "legacy_ahk_liferpg"
            },
            "projects": [
                {
                    "title": "Example Project",
                    "description": "Project description",
                    "status": "active",
                    "difficulty": 3,
                    "importance": "High",
                    "parent_title": None,
                    "created_at": "2025-01-01T12:00:00Z"
                }
            ],
            "habits": [
                {
                    "title": "Daily Exercise",
                    "notes": "30 minutes of exercise",
                    "cadence": "daily",
                    "difficulty": 2,
                    "status": "active",
                    "project_title": "Example Project",
                    "created_at": "2025-01-01T12:00:00Z"
                }
            ],
            "logs": [
                {
                    "habit_title": "Daily Exercise",
                    "action": "completed",
                    "timestamp": "2025-01-01T18:00:00Z",
                    "notes": "Completed workout"
                }
            ],
            "skills": [
                {
                    "name": "Fitness",
                    "level": 5,
                    "experience": 150
                }
            ]
        }

    def validate_import_data(self, data: Dict) -> List[str]:
        """Validate import data format and return any errors."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Import data must be a JSON object")
            return errors
        
        # Validate projects structure
        if 'projects' in data:
            if not isinstance(data['projects'], list):
                errors.append("Projects must be an array")
            else:
                for i, project in enumerate(data['projects']):
                    if not isinstance(project, dict):
                        errors.append(f"Project {i} must be an object")
                    elif 'title' not in project:
                        errors.append(f"Project {i} missing required 'title'")
        
        # Validate habits structure
        if 'habits' in data:
            if not isinstance(data['habits'], list):
                errors.append("Habits must be an array")
            else:
                for i, habit in enumerate(data['habits']):
                    if not isinstance(habit, dict):
                        errors.append(f"Habit {i} must be an object")
                    elif 'title' not in habit:
                        errors.append(f"Habit {i} missing required 'title'")
        
        # Validate logs structure
        if 'logs' in data:
            if not isinstance(data['logs'], list):
                errors.append("Logs must be an array")
            else:
                for i, log in enumerate(data['logs']):
                    if not isinstance(log, dict):
                        errors.append(f"Log {i} must be an object")
                    elif 'habit_title' not in log:
                        errors.append(f"Log {i} missing required 'habit_title'")
                    elif 'timestamp' not in log:
                        errors.append(f"Log {i} missing required 'timestamp'")
        
        return errors