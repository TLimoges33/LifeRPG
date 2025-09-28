"""
Health check and system status monitoring for LifeRPG.
Provides comprehensive health monitoring for all system components.
"""

import asyncio
import time
import psutil
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

health_router = APIRouter(prefix="/api/v1/health", tags=["Health"])


class SystemHealthMonitor:
    """Monitor system health and component status."""
    
    def __init__(self):
        self.last_check = None
        self.component_status = {}
    
    async def check_database_health(self) -> Dict:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test database connection
            with sqlite3.connect('modern_dev.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                # Check table existence
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('users', 'habits', 'projects')
                """)
                tables = [row[0] for row in cursor.fetchall()]
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "tables_found": tables,
                "expected_tables": ["users", "habits", "projects"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_ai_models_health(self) -> Dict:
        """Check AI models availability and performance."""
        try:
            from .huggingface_ai import ai_service
            
            start_time = time.time()
            
            # Test model loading
            models_status = {}
            
            # Test sentiment analysis
            try:
                result = await ai_service.analyze_sentiment("Test message")
                models_status["sentiment_analysis"] = {
                    "status": "healthy",
                    "model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "test_result": result
                }
            except Exception as e:
                models_status["sentiment_analysis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Test natural language inference
            try:
                result = await ai_service.classify_text(
                    "Complete daily exercise", 
                    ["fitness", "work", "hobby"]
                )
                models_status["text_classification"] = {
                    "status": "healthy",
                    "model": "facebook/bart-large-mnli",
                    "test_result": result
                }
            except Exception as e:
                models_status["text_classification"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            response_time = (time.time() - start_time) * 1000
            
            overall_status = "healthy" if all(
                m["status"] == "healthy" for m in models_status.values()
            ) else "degraded"
            
            return {
                "status": overall_status,
                "response_time_ms": response_time,
                "models": models_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI models health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_system_resources(self) -> Dict:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # System load
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            return {
                "status": "healthy",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "status": "healthy" if cpu_percent < 80 else "warning"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "status": "healthy" if memory.percent < 80 else "warning"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "status": "healthy" if (disk.used / disk.total) < 0.8 else "warning"
                },
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_api_endpoints(self) -> Dict:
        """Check critical API endpoints."""
        import httpx
        
        endpoints = [
            "/api/v1/users/profile",
            "/api/v1/habits",
            "/api/v1/projects",
            "/api/v1/ai/analyze"
        ]
        
        endpoint_status = {}
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    # This would need proper authentication in production
                    response = await client.get(f"http://localhost:8000{endpoint}")
                    response_time = (time.time() - start_time) * 1000
                    
                    endpoint_status[endpoint] = {
                        "status": "healthy" if response.status_code < 500 else "unhealthy",
                        "status_code": response.status_code,
                        "response_time_ms": response_time
                    }
                    
                except Exception as e:
                    endpoint_status[endpoint] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
        
        overall_status = "healthy" if all(
            e["status"] == "healthy" for e in endpoint_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "endpoints": endpoint_status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def comprehensive_health_check(self) -> Dict:
        """Run comprehensive health check across all components."""
        start_time = time.time()
        
        # Run all health checks concurrently
        db_health, ai_health, system_health, api_health = await asyncio.gather(
            self.check_database_health(),
            self.check_ai_models_health(),
            asyncio.to_thread(self.check_system_resources),
            self.check_api_endpoints(),
            return_exceptions=True
        )
        
        # Handle any exceptions from concurrent execution
        components = {
            "database": db_health if not isinstance(db_health, Exception) else {"status": "error", "error": str(db_health)},
            "ai_models": ai_health if not isinstance(ai_health, Exception) else {"status": "error", "error": str(ai_health)},
            "system_resources": system_health if not isinstance(system_health, Exception) else {"status": "error", "error": str(system_health)},
            "api_endpoints": api_health if not isinstance(api_health, Exception) else {"status": "error", "error": str(api_health)}
        }
        
        # Determine overall system health
        component_statuses = [comp.get("status", "error") for comp in components.values()]
        
        if all(status == "healthy" for status in component_statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" or status == "error" for status in component_statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        total_time = (time.time() - start_time) * 1000
        
        self.last_check = datetime.now()
        self.component_status = components
        
        return {
            "overall_status": overall_status,
            "components": components,
            "health_check_duration_ms": total_time,
            "timestamp": self.last_check.isoformat(),
            "version": "1.0.0",
            "uptime_seconds": time.time() - psutil.boot_time()
        }


# Global health monitor instance
health_monitor = SystemHealthMonitor()


@health_router.get("/")
async def health_check():
    """Quick health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "LifeRPG Backend"
    }


@health_router.get("/comprehensive")
async def comprehensive_health():
    """Comprehensive health check of all system components."""
    return await health_monitor.comprehensive_health_check()


@health_router.get("/database")
async def database_health():
    """Check database health specifically."""
    return await health_monitor.check_database_health()


@health_router.get("/ai")
async def ai_models_health():
    """Check AI models health specifically."""
    return await health_monitor.check_ai_models_health()


@health_router.get("/system")
async def system_health():
    """Check system resources."""
    return health_monitor.check_system_resources()


@health_router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check."""
    health_result = await health_monitor.comprehensive_health_check()
    
    if health_result["overall_status"] == "unhealthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"ready": True, "timestamp": datetime.now().isoformat()}


@health_router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check."""
    # Basic liveness - service is running
    return {"alive": True, "timestamp": datetime.now().isoformat()}