"""
Performance monitoring and analytics for LifeRPG AI features.
Tracks usage, performance, and accuracy metrics.
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import wraps
import json
from dataclasses import dataclass, asdict
from collections import defaultdict

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AIMetric:
    """Data class for AI performance metrics."""
    timestamp: datetime
    operation: str
    duration_ms: float
    success: bool
    user_id: Optional[int] = None
    input_length: Optional[int] = None
    output_length: Optional[int] = None
    model_name: Optional[str] = None
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None


class AIPerformanceMonitor:
    """Monitor and track AI performance metrics."""
    
    def __init__(self):
        self.metrics: List[AIMetric] = []
        self.daily_stats = defaultdict(lambda: defaultdict(int))
        
    def track_operation(self, operation_name: str, model_name: str = None):
        """Decorator to track AI operation performance."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                result = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    logger.error(f"AI operation {operation_name} failed: {e}")
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Extract input/output lengths if possible
                    input_length = None
                    output_length = None
                    confidence_score = None
                    
                    if args and isinstance(args[0], str):
                        input_length = len(args[0])
                    
                    if success and result:
                        if isinstance(result, dict):
                            output_length = len(str(result))
                            confidence_score = result.get('confidence')
                        elif isinstance(result, str):
                            output_length = len(result)
                    
                    # Create metric
                    metric = AIMetric(
                        timestamp=datetime.now(),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=success,
                        input_length=input_length,
                        output_length=output_length,
                        model_name=model_name,
                        error_message=error_message,
                        confidence_score=confidence_score
                    )
                    
                    self.record_metric(metric)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    logger.error(f"AI operation {operation_name} failed: {e}")
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    metric = AIMetric(
                        timestamp=datetime.now(),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=success,
                        model_name=model_name,
                        error_message=error_message
                    )
                    
                    self.record_metric(metric)
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def record_metric(self, metric: AIMetric):
        """Record a performance metric."""
        self.metrics.append(metric)
        
        # Update daily stats
        date_key = metric.timestamp.strftime('%Y-%m-%d')
        self.daily_stats[date_key]['total_requests'] += 1
        
        if metric.success:
            self.daily_stats[date_key]['successful_requests'] += 1
            self.daily_stats[date_key]['total_duration_ms'] += metric.duration_ms
        else:
            self.daily_stats[date_key]['failed_requests'] += 1
        
        # Log structured metric
        logger.info(
            "ai_metric",
            extra={
                'operation': metric.operation,
                'duration_ms': metric.duration_ms,
                'success': metric.success,
                'model_name': metric.model_name,
                'timestamp': metric.timestamp.isoformat()
            }
        )
        
        # Keep only recent metrics to prevent memory bloat
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-5000:]  # Keep last 5000
    
    def get_performance_summary(self, days: int = 7) -> Dict:
        """Get performance summary for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_date]
        
        if not recent_metrics:
            return {"message": "No metrics available"}
        
        # Calculate statistics
        total_requests = len(recent_metrics)
        successful_requests = sum(1 for m in recent_metrics if m.success)
        failed_requests = total_requests - successful_requests
        
        durations = [m.duration_ms for m in recent_metrics if m.success]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        
        # Operation breakdown
        operation_stats = defaultdict(lambda: {'count': 0, 'avg_duration': 0})
        operation_durations = defaultdict(list)
        
        for metric in recent_metrics:
            if metric.success:
                operation_stats[metric.operation]['count'] += 1
                operation_durations[metric.operation].append(metric.duration_ms)
        
        for op, durations_list in operation_durations.items():
            if durations_list:
                operation_stats[op]['avg_duration'] = sum(durations_list) / len(durations_list)
        
        # Model performance
        model_stats = defaultdict(lambda: {'count': 0, 'success_rate': 0})
        for metric in recent_metrics:
            if metric.model_name:
                model_stats[metric.model_name]['count'] += 1
                if metric.success:
                    model_stats[metric.model_name]['success_rate'] += 1
        
        for model, stats in model_stats.items():
            if stats['count'] > 0:
                stats['success_rate'] = stats['success_rate'] / stats['count']
        
        return {
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'avg_duration_ms': avg_duration,
                'max_duration_ms': max_duration,
                'min_duration_ms': min_duration
            },
            'operations': dict(operation_stats),
            'models': dict(model_stats),
            'period_days': days
        }
    
    def get_real_time_stats(self) -> Dict:
        """Get real-time performance statistics."""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_minute = now - timedelta(minutes=1)
        
        hour_metrics = [m for m in self.metrics if m.timestamp >= last_hour]
        minute_metrics = [m for m in self.metrics if m.timestamp >= last_minute]
        
        return {
            'last_hour': {
                'total_requests': len(hour_metrics),
                'successful_requests': sum(1 for m in hour_metrics if m.success),
                'avg_duration_ms': sum(m.duration_ms for m in hour_metrics if m.success) / max(len([m for m in hour_metrics if m.success]), 1)
            },
            'last_minute': {
                'total_requests': len(minute_metrics),
                'successful_requests': sum(1 for m in minute_metrics if m.success)
            },
            'timestamp': now.isoformat()
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        if format == 'json':
            return json.dumps([asdict(m) for m in self.metrics], default=str, indent=2)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'timestamp', 'operation', 'duration_ms', 'success', 
                'model_name', 'input_length', 'output_length', 'confidence_score'
            ])
            writer.writeheader()
            
            for metric in self.metrics:
                writer.writerow(asdict(metric))
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


class AIAccuracyTracker:
    """Track AI accuracy and user feedback."""
    
    def __init__(self):
        self.feedback_data = []
    
    def record_user_feedback(self, operation: str, ai_result: Dict, user_feedback: Dict):
        """Record user feedback on AI predictions/suggestions."""
        feedback_entry = {
            'timestamp': datetime.now(),
            'operation': operation,
            'ai_result': ai_result,
            'user_feedback': user_feedback,
            'accuracy_score': self._calculate_accuracy(ai_result, user_feedback)
        }
        
        self.feedback_data.append(feedback_entry)
        
        logger.info(
            "ai_accuracy_feedback",
            extra={
                'operation': operation,
                'accuracy_score': feedback_entry['accuracy_score'],
                'timestamp': feedback_entry['timestamp'].isoformat()
            }
        )
    
    def _calculate_accuracy(self, ai_result: Dict, user_feedback: Dict) -> float:
        """Calculate accuracy score based on user feedback."""
        # This would be implemented based on specific feedback mechanisms
        # For now, return a simple score based on user satisfaction
        satisfaction = user_feedback.get('satisfaction', 0)  # 1-5 scale
        return satisfaction / 5.0
    
    def get_accuracy_summary(self, days: int = 30) -> Dict:
        """Get accuracy summary for operations."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = [f for f in self.feedback_data if f['timestamp'] >= cutoff_date]
        
        if not recent_feedback:
            return {"message": "No accuracy data available"}
        
        # Calculate per-operation accuracy
        operation_accuracy = defaultdict(list)
        for feedback in recent_feedback:
            operation_accuracy[feedback['operation']].append(feedback['accuracy_score'])
        
        summary = {}
        for operation, scores in operation_accuracy.items():
            summary[operation] = {
                'avg_accuracy': sum(scores) / len(scores),
                'sample_count': len(scores),
                'max_accuracy': max(scores),
                'min_accuracy': min(scores)
            }
        
        overall_scores = [f['accuracy_score'] for f in recent_feedback]
        summary['overall'] = {
            'avg_accuracy': sum(overall_scores) / len(overall_scores),
            'sample_count': len(overall_scores)
        }
        
        return summary


# Global instances
performance_monitor = AIPerformanceMonitor()
accuracy_tracker = AIAccuracyTracker()


# Convenience decorators for common operations
def track_habit_parsing(func):
    """Track habit parsing performance."""
    return performance_monitor.track_operation("habit_parsing", "roberta-sentiment")(func)

def track_success_prediction(func):
    """Track success prediction performance."""
    return performance_monitor.track_operation("success_prediction", "bart-mnli")(func)

def track_suggestion_generation(func):
    """Track suggestion generation performance."""
    return performance_monitor.track_operation("suggestion_generation")(func)


# FastAPI endpoints for monitoring
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])
security = HTTPBearer()

@monitoring_router.get("/ai/performance")
async def get_ai_performance(days: int = 7):
    """Get AI performance summary."""
    return performance_monitor.get_performance_summary(days)

@monitoring_router.get("/ai/realtime")
async def get_realtime_stats():
    """Get real-time AI performance stats."""
    return performance_monitor.get_real_time_stats()

@monitoring_router.get("/ai/accuracy")
async def get_accuracy_stats(days: int = 30):
    """Get AI accuracy statistics."""
    return accuracy_tracker.get_accuracy_summary(days)

@monitoring_router.post("/ai/feedback")
async def submit_ai_feedback(
    operation: str,
    ai_result: dict,
    user_feedback: dict
):
    """Submit feedback on AI operation accuracy."""
    accuracy_tracker.record_user_feedback(operation, ai_result, user_feedback)
    return {"message": "Feedback recorded successfully"}


# Export metrics endpoint
@monitoring_router.get("/ai/metrics/export")
async def export_ai_metrics(format: str = "json"):
    """Export AI metrics for analysis."""
    return {
        "data": performance_monitor.export_metrics(format),
        "format": format,
        "exported_at": datetime.now().isoformat()
    }