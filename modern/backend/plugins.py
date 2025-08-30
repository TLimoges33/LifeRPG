"""
LifeRPG Plugin System - Backend Implementation

This module implements the server-side components of the LifeRPG plugin system:
- Plugin registry and metadata storage
- Plugin sandboxing and execution
- Plugin API endpoints
- Plugin permissions and security

The plugin system uses WebAssembly (WASM) for secure sandboxing of plugin code.
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

from db import get_db
import models
from plugin_runtime import get_plugin_runtime

# Configure logging
logger = logging.getLogger("liferpg.plugins")

# Define plugin models
class PluginPermission(str, Enum):
    """Permissions that can be granted to plugins."""
    
    # Data access permissions
    HABITS_READ = "habits:read"
    HABITS_WRITE = "habits:write"
    PROJECTS_READ = "projects:read"
    PROJECTS_WRITE = "projects:write"
    USERS_READ = "users:read"
    
    # UI permissions
    UI_DASHBOARD = "ui:dashboard"
    UI_SETTINGS = "ui:settings"
    UI_REPORTS = "ui:reports"
    
    # System permissions
    STORAGE_PLUGIN = "storage:plugin"
    NETWORK_SAME_ORIGIN = "network:same-origin"
    NETWORK_EXTERNAL = "network:external"


class PluginStatus(str, Enum):
    """Status of a plugin in the system."""
    
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class ResourceLimits(BaseModel):
    """Resource limits for plugin execution."""
    
    memory_mb: int = Field(16, description="Memory limit in MB")
    storage_mb: int = Field(5, description="Storage limit in MB")
    cpu_limit: str = Field("moderate", description="CPU limit (low, moderate, high)")
    
    @validator("cpu_limit")
    def validate_cpu_limit(cls, v):
        allowed = ["low", "moderate", "high"]
        if v not in allowed:
            raise ValueError(f"CPU limit must be one of {allowed}")
        return v


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""
    
    id: str = Field(..., description="Unique plugin identifier")
    name: str = Field(..., description="Display name of the plugin")
    version: str = Field(..., description="Plugin version (semver)")
    author: str = Field(..., description="Plugin author")
    description: str = Field(..., description="Plugin description")
    homepage: Optional[str] = Field(None, description="Plugin homepage URL")
    target_api_version: str = Field(..., description="Target API version")
    min_app_version: str = Field(..., description="Minimum app version required")
    permissions: List[PluginPermission] = Field([], description="Required permissions")
    extension_points: List[str] = Field([], description="Extension points used")
    entry_point: str = Field("initialize", description="Main entry point function")
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: PluginStatus = Field(PluginStatus.PENDING_REVIEW)


# Database models
class DBPlugin(Base):
    """Database model for plugin metadata."""
    
    __tablename__ = "plugins"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    homepage = Column(String, nullable=True)
    target_api_version = Column(String, nullable=False)
    min_app_version = Column(String, nullable=False)
    permissions = Column(Text, nullable=False)  # JSON
    extension_points = Column(Text, nullable=False)  # JSON
    entry_point = Column(String, nullable=False)
    resource_limits = Column(Text, nullable=False)  # JSON
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String, nullable=False, default=PluginStatus.PENDING_REVIEW.value)
    
    def to_metadata(self) -> PluginMetadata:
        """Convert database model to PluginMetadata."""
        return PluginMetadata(
            id=self.id,
            name=self.name,
            version=self.version,
            author=self.author,
            description=self.description,
            homepage=self.homepage,
            target_api_version=self.target_api_version,
            min_app_version=self.min_app_version,
            permissions=json.loads(self.permissions),
            extension_points=json.loads(self.extension_points),
            entry_point=self.entry_point,
            resource_limits=ResourceLimits(**json.loads(self.resource_limits)),
            created_at=self.created_at,
            updated_at=self.updated_at,
            status=PluginStatus(self.status),
        )
    
    @classmethod
    def from_metadata(cls, metadata: PluginMetadata) -> "DBPlugin":
        """Create database model from PluginMetadata."""
        return cls(
            id=metadata.id,
            name=metadata.name,
            version=metadata.version,
            author=metadata.author,
            description=metadata.description,
            homepage=metadata.homepage,
            target_api_version=metadata.target_api_version,
            min_app_version=metadata.min_app_version,
            permissions=json.dumps([p.value for p in metadata.permissions]),
            extension_points=json.dumps(metadata.extension_points),
            entry_point=metadata.entry_point,
            resource_limits=json.dumps(metadata.resource_limits.dict()),
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            status=metadata.status.value,
        )


class PluginManager:
    """Manages plugin lifecycle and execution."""
    
    def __init__(self, db: Session, plugins_dir: Path):
        self.db = db
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Plugin manager initialized with plugins directory: {plugins_dir}")
    
    async def register_plugin(self, metadata: PluginMetadata, wasm_binary: bytes) -> str:
        """Register a new plugin."""
        # Check for existing plugin
        existing = self.db.query(DBPlugin).filter(DBPlugin.id == metadata.id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Plugin {metadata.id} already exists")
        
        # Save plugin binary
        plugin_dir = self.plugins_dir / metadata.id
        plugin_dir.mkdir(exist_ok=True)
        
        with open(plugin_dir / "plugin.wasm", "wb") as f:
            f.write(wasm_binary)
        
        with open(plugin_dir / "metadata.json", "w") as f:
            f.write(metadata.json())
        
        # Save to database
        db_plugin = DBPlugin.from_metadata(metadata)
        self.db.add(db_plugin)
        self.db.commit()
        
        # Load plugin if it's active
        if metadata.status == PluginStatus.ACTIVE:
            runtime = await get_plugin_runtime()
            success = await runtime.load_plugin(metadata.id, metadata, wasm_binary, self.db)
            if not success:
                logger.warning(f"Failed to load plugin {metadata.id} at registration")
        
        logger.info(f"Registered plugin: {metadata.id} v{metadata.version}")
        return metadata.id
    
    async def update_plugin(self, plugin_id: str, metadata: PluginMetadata, wasm_binary: Optional[bytes] = None) -> None:
        """Update an existing plugin."""
        # Check for existing plugin
        existing = self.db.query(DBPlugin).filter(DBPlugin.id == plugin_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
        # Update metadata
        metadata.updated_at = datetime.utcnow()
        plugin_dir = self.plugins_dir / plugin_id
        
        with open(plugin_dir / "metadata.json", "w") as f:
            f.write(metadata.json())
        
        # Update binary if provided
        if wasm_binary:
            with open(plugin_dir / "plugin.wasm", "wb") as f:
                f.write(wasm_binary)
        
        # Update database
        db_plugin = DBPlugin.from_metadata(metadata)
        db_plugin.id = plugin_id  # Ensure ID remains the same
        
        self.db.query(DBPlugin).filter(DBPlugin.id == plugin_id).update({
            "name": db_plugin.name,
            "version": db_plugin.version,
            "author": db_plugin.author,
            "description": db_plugin.description,
            "homepage": db_plugin.homepage,
            "target_api_version": db_plugin.target_api_version,
            "min_app_version": db_plugin.min_app_version,
            "permissions": db_plugin.permissions,
            "extension_points": db_plugin.extension_points,
            "entry_point": db_plugin.entry_point,
            "resource_limits": db_plugin.resource_limits,
            "updated_at": db_plugin.updated_at,
            "status": db_plugin.status,
        })
        self.db.commit()
        
        logger.info(f"Updated plugin: {plugin_id} to v{metadata.version}")
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get plugin metadata."""
        plugin = self.db.query(DBPlugin).filter(DBPlugin.id == plugin_id).first()
        if not plugin:
            return None
        return plugin.to_metadata()
    
    async def list_plugins(self, status: Optional[PluginStatus] = None) -> List[PluginMetadata]:
        """List all plugins."""
        query = self.db.query(DBPlugin)
        if status:
            query = query.filter(DBPlugin.status == status.value)
        
        plugins = query.all()
        return [p.to_metadata() for p in plugins]
    
    async def set_plugin_status(self, plugin_id: str, status: PluginStatus) -> None:
        """Set plugin status."""
        plugin = self.db.query(DBPlugin).filter(DBPlugin.id == plugin_id).first()
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
        old_status = PluginStatus(plugin.status)
        plugin.status = status.value
        plugin.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Handle runtime loading/unloading
        runtime = await get_plugin_runtime()
        
        if status == PluginStatus.ACTIVE and old_status != PluginStatus.ACTIVE:
            # Load the plugin
            plugin_dir = self.plugins_dir / plugin_id
            wasm_file = plugin_dir / "plugin.wasm"
            
            if wasm_file.exists():
                with open(wasm_file, "rb") as f:
                    wasm_binary = f.read()
                
                metadata = plugin.to_metadata()
                success = await runtime.load_plugin(plugin_id, metadata, wasm_binary, self.db)
                if not success:
                    logger.error(f"Failed to load plugin {plugin_id}")
        
        elif status != PluginStatus.ACTIVE and old_status == PluginStatus.ACTIVE:
            # Unload the plugin
            await runtime.unload_plugin(plugin_id)
        
        logger.info(f"Set plugin {plugin_id} status to {status.value}")
    
    async def delete_plugin(self, plugin_id: str) -> None:
        """Delete a plugin."""
        plugin = self.db.query(DBPlugin).filter(DBPlugin.id == plugin_id).first()
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
        # Unload from runtime if active
        runtime = await get_plugin_runtime()
        await runtime.unload_plugin(plugin_id)
        
        # Remove files
        plugin_dir = self.plugins_dir / plugin_id
        if plugin_dir.exists():
            import shutil
            shutil.rmtree(plugin_dir)
        
        # Remove from database
        self.db.delete(plugin)
        self.db.commit()
        
        logger.info(f"Deleted plugin: {plugin_id}")
    
    async def get_extension_points(self) -> Dict[str, List[Any]]:
        """Get all extension points from loaded plugins."""
        runtime = await get_plugin_runtime()
        return runtime.get_all_extension_points()


# API Router
router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])

# Dependency to get plugin manager
async def get_plugin_manager(db: Session = Depends(get_db)):
    plugins_dir = Path(os.getenv("PLUGINS_DIR", "plugins"))
    return PluginManager(db, plugins_dir)


# API Endpoints
@router.get("/", response_model=List[PluginMetadata])
async def list_plugins(
    status: Optional[PluginStatus] = None,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """List all plugins."""
    return await plugin_manager.list_plugins(status)


@router.get("/{plugin_id}", response_model=PluginMetadata)
async def get_plugin(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Get plugin metadata."""
    plugin = await plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
    return plugin


@router.post("/", response_model=dict)
async def register_plugin(
    metadata: PluginMetadata,
    wasm_file: UploadFile = File(...),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Register a new plugin."""
    wasm_binary = await wasm_file.read()
    plugin_id = await plugin_manager.register_plugin(metadata, wasm_binary)
    return {"id": plugin_id, "status": "registered"}


@router.put("/{plugin_id}", response_model=dict)
async def update_plugin(
    plugin_id: str,
    metadata: PluginMetadata,
    wasm_file: Optional[UploadFile] = None,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Update an existing plugin."""
    wasm_binary = await wasm_file.read() if wasm_file else None
    await plugin_manager.update_plugin(plugin_id, metadata, wasm_binary)
    return {"id": plugin_id, "status": "updated"}


@router.patch("/{plugin_id}/status", response_model=dict)
async def set_plugin_status(
    plugin_id: str,
    status: PluginStatus,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Set plugin status."""
    await plugin_manager.set_plugin_status(plugin_id, status)
    return {"id": plugin_id, "status": status}


@router.delete("/{plugin_id}", response_model=dict)
async def delete_plugin(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Delete a plugin."""
    await plugin_manager.delete_plugin(plugin_id)
    return {"id": plugin_id, "status": "deleted"}


@router.get("/extension-points", response_model=dict)
async def get_extension_points(
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Get all extension points from loaded plugins."""
    extension_points = await plugin_manager.get_extension_points()
    return {"extension_points": extension_points}


@router.get("/{plugin_id}/wasm")
async def get_plugin_wasm(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """Get the WASM binary for a plugin."""
    plugin = await plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
    
    plugin_dir = plugin_manager.plugins_dir / plugin_id
    wasm_file = plugin_dir / "plugin.wasm"
    
    if not wasm_file.exists():
        raise HTTPException(status_code=404, detail=f"WASM binary not found for plugin {plugin_id}")
    
    from fastapi.responses import FileResponse
    return FileResponse(wasm_file, media_type="application/wasm")


# Function to add plugin system to FastAPI app
def setup_plugin_system(app: FastAPI):
    """Set up the plugin system in a FastAPI application."""
    app.include_router(router)
    
    # Make sure plugins directory exists
    plugins_dir = Path(os.getenv("PLUGINS_DIR", "plugins"))
    plugins_dir.mkdir(exist_ok=True, parents=True)
    
    logger.info("Plugin system initialized")
    
    return app
