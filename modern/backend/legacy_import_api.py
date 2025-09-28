"""
Legacy Import API Endpoints - FastAPI endpoints for importing AHK data
"""
from fastapi import UploadFile, HTTPException, Depends, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import json

# These would be added to the main app.py file

def add_legacy_import_endpoints(app):
    """Add legacy import endpoints to the FastAPI app."""
    
    @app.post('/api/v1/import/legacy/json')
    async def import_legacy_json(
        file: UploadFile = File(...),
        user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Import legacy data from JSON export file."""
        if not file.filename.endswith('.json'):
            raise HTTPException(400, "File must be a JSON file")
        
        try:
            content = await file.read()
            data = json.loads(content)
            
            # Validate the data
            from .legacy_importer import LegacyImporter
            importer = LegacyImporter(db)
            validation_errors = importer.validate_import_data(data)
            
            if validation_errors:
                raise HTTPException(400, {
                    "message": "Invalid import data format",
                    "errors": validation_errors
                })
            
            # Import the data
            results = importer.import_json_export(data, user.id)
            
            return {
                "success": True,
                "message": "Legacy data imported successfully",
                "results": results
            }
            
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON format")
        except Exception as e:
            raise HTTPException(500, f"Import failed: {str(e)}")
    
    @app.post('/api/v1/import/legacy/csv')
    async def import_legacy_csv(
        file: UploadFile = File(...),
        import_type: str = Form(...),  # 'projects' or 'habits' or 'logs'
        user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Import legacy data from CSV export file."""
        if not file.filename.endswith('.csv'):
            raise HTTPException(400, "File must be a CSV file")
        
        if import_type not in ['projects', 'habits', 'logs']:
            raise HTTPException(400, "import_type must be: projects, habits, or logs")
        
        try:
            content = await file.read()
            
            from .legacy_importer import LegacyImporter
            importer = LegacyImporter(db)
            results = importer.import_csv_export(content, user.id)
            
            return {
                "success": True,
                "message": f"Legacy {import_type} imported successfully",
                "results": results
            }
            
        except Exception as e:
            raise HTTPException(500, f"Import failed: {str(e)}")
    
    @app.get('/api/v1/import/legacy/template')
    async def get_import_template(
        user=Depends(get_current_user)
    ):
        """Get a template JSON structure for importing legacy data."""
        from .legacy_importer import LegacyImporter
        importer = LegacyImporter(None)  # No DB needed for template
        
        return importer.generate_import_template()
    
    @app.post('/api/v1/import/legacy/validate')
    async def validate_import_data(
        file: UploadFile = File(...),
        user=Depends(get_current_user)
    ):
        """Validate legacy import data without importing."""
        if not file.filename.endswith('.json'):
            raise HTTPException(400, "File must be a JSON file")
        
        try:
            content = await file.read()
            data = json.loads(content)
            
            from .legacy_importer import LegacyImporter
            importer = LegacyImporter(None)
            validation_errors = importer.validate_import_data(data)
            
            return {
                "valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "data_summary": {
                    "projects": len(data.get('projects', [])),
                    "habits": len(data.get('habits', [])),
                    "logs": len(data.get('logs', [])),
                    "skills": len(data.get('skills', []))
                }
            }
            
        except json.JSONDecodeError:
            raise HTTPException(400, "Invalid JSON format")
        except Exception as e:
            raise HTTPException(500, f"Validation failed: {str(e)}")

    return app