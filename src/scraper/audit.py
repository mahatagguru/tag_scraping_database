"""
Comprehensive audit logging utilities for the TAG Grading Scraper system.

This module provides structured logging with error handling, context tracking,
performance monitoring, and database persistence for audit logs.
"""

import json
import traceback
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
from functools import wraps
import inspect
import os
import sys

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import models after ensuring they're available
try:
    from models import AuditLog
    from db import get_db_session
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("Warning: Database models not available, audit logging will be file-based only")

# Configure standard logging
def setup_logging():
    """Setup logging with proper directory handling."""
    # Ensure logs directory exists
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir, exist_ok=True)
        except (OSError, PermissionError):
            # If we can't create logs directory, just use console logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            return
    
    # Try to setup file logging
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, 'audit.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
    except (OSError, PermissionError):
        # Fallback to console-only logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

class AuditLogger:
    """Main audit logging class with comprehensive error handling and context tracking."""
    
    def __init__(self, component: str = None):
        self.component = component or self._get_calling_component()
        self.session: Optional[Session] = None
    
    def _get_calling_component(self) -> str:
        """Automatically determine the calling component from the call stack."""
        try:
            # Get the calling frame (skip this method and the decorator)
            frame = inspect.currentframe()
            for _ in range(3):  # Skip a few frames to get to the actual caller
                if frame:
                    frame = frame.f_back
                else:
                    break
            
            if frame:
                module_name = frame.f_globals.get('__name__', 'unknown')
                # Extract component name from module path
                if '.' in module_name:
                    return module_name.split('.')[-1]
                return module_name
        except Exception:
            pass
        return 'unknown'
    
    def _get_db_session(self) -> Optional[Session]:
        """Get a database session for audit logging."""
        if not MODELS_AVAILABLE:
            return None
        
        try:
            if not self.session or self.session.is_closed:
                self.session = get_db_session()
            return self.session
        except Exception as e:
            logger.error(f"Failed to get database session for audit logging: {e}")
            return None
    
    def _log_to_database(self, level: str, message: str, **kwargs) -> bool:
        """Log audit entry to database."""
        if not MODELS_AVAILABLE:
            return False
        
        try:
            session = self._get_db_session()
            if not session:
                return False
            
            # Create audit log entry
            audit_entry = AuditLog(
                level=level.upper(),
                component=self.component,
                operation=kwargs.get('operation'),
                status=kwargs.get('status'),
                error_code=kwargs.get('error_code'),
                error_message=kwargs.get('error_message'),
                context=kwargs.get('context'),
                message=message,
                stack_trace=kwargs.get('stack_trace'),
                user_agent=kwargs.get('user_agent'),
                ip_address=kwargs.get('ip_address'),
                execution_time_ms=kwargs.get('execution_time_ms'),
                created_at=datetime.now(timezone.utc)
            )
            
            session.add(audit_entry)
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in audit logging: {e}")
            if session:
                session.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error in audit logging: {e}")
            return False
    
    def _log_to_file(self, level: str, message: str, **kwargs):
        """Log audit entry to file as fallback."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.upper(),
            'component': self.component,
            'message': message,
            **kwargs
        }
        
        # Remove None values for cleaner logs
        log_entry = {k: v for k, v in log_entry.items() if v is not None}
        
        logger.log(
            getattr(logging, level.upper(), logging.INFO),
            f"AUDIT: {json.dumps(log_entry, default=str)}"
        )
    
    def log(self, level: str, message: str, **kwargs):
        """Log an audit entry with comprehensive context."""
        # Ensure level is valid
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level.upper() not in valid_levels:
            level = 'INFO'
        
        # Try database logging first
        db_success = self._log_to_database(level, message, **kwargs)
        
        # Always log to file as backup
        self._log_to_file(level, message, **kwargs)
        
        return db_success
    
    def info(self, message: str, **kwargs):
        """Log info level audit entry."""
        return self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level audit entry."""
        return self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error level audit entry with error details."""
        error_context = {}
        
        if error:
            error_context.update({
                'error_code': getattr(error, 'code', None),
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'error_type': type(error).__name__
            })
        
        return self.log('ERROR', message, **{**kwargs, **error_context})
    
    def critical(self, message: str, error: Exception = None, **kwargs):
        """Log critical level audit entry."""
        return self.log('CRITICAL', message, error=error, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level audit entry."""
        return self.log('DEBUG', message, **kwargs)
    
    def log_operation(self, operation: str, status: str = 'SUCCESS', **kwargs):
        """Log operation-specific audit entry."""
        return self.log('INFO', f"Operation: {operation}", 
                       operation=operation, status=status, **kwargs)
    
    def log_performance(self, operation: str, execution_time_ms: int, **kwargs):
        """Log performance-related audit entry."""
        return self.log('INFO', f"Performance: {operation} completed in {execution_time_ms}ms",
                       operation=operation, execution_time_ms=execution_time_ms, **kwargs)
    
    def log_error_with_context(self, message: str, error: Exception, 
                              operation: str = None, context: Dict[str, Any] = None):
        """Log error with comprehensive context and operation details."""
        error_context = {
            'operation': operation,
            'status': 'FAILURE',
            'error_code': getattr(error, 'code', None),
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'error_type': type(error).__name__,
            'context': context or {}
        }
        
        return self.log('ERROR', message, **error_context)
    
    def close(self):
        """Close the audit logger and clean up resources."""
        if self.session and not self.session.is_closed:
            self.session.close()

# Global audit logger instance
_global_audit_logger = None

def get_audit_logger(component: str = None) -> AuditLogger:
    """Get a global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger(component)
    return _global_audit_logger

def log_audit(level: str, message: str, context: Dict[str, Any] = None, **kwargs):
    """Legacy function for backward compatibility."""
    audit_logger = get_audit_logger()
    return audit_logger.log(level, message, context=context, **kwargs)

# Decorators for automatic audit logging

def audit_operation(operation_name: str = None, log_args: bool = False, log_result: bool = False):
    """Decorator to automatically audit function operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            operation = operation_name or func.__name__
            start_time = time.time()
            
            # Log operation start
            audit_logger.log_operation(operation, status='STARTED')
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Log successful completion
                audit_logger.log_performance(operation, execution_time_ms, status='SUCCESS')
                
                if log_result and result is not None:
                    audit_logger.info(f"Operation {operation} completed successfully", 
                                    operation=operation, context={'result_type': type(result).__name__})
                
                return result
                
            except Exception as e:
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Log error with context
                context = {}
                if log_args:
                    context['args_count'] = len(args)
                    context['kwargs_keys'] = list(kwargs.keys())
                
                audit_logger.log_error_with_context(
                    f"Operation {operation} failed",
                    e,
                    operation=operation,
                    context=context
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator

@contextmanager
def audit_context(operation: str, component: str = None, **context):
    """Context manager for auditing operations with automatic timing."""
    audit_logger = get_audit_logger(component)
    start_time = time.time()
    
    try:
        audit_logger.log_operation(operation, status='STARTED', **context)
        yield audit_logger
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_performance(operation, execution_time_ms, status='SUCCESS', **context)
        
    except Exception as e:
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log error
        audit_logger.log_error_with_context(
            f"Operation {operation} failed",
            e,
            operation=operation,
            context=context
        )
        raise

# Utility functions for common audit scenarios

def log_scraping_start(sport: str, year: str = None, set_name: str = None, **kwargs):
    """Log the start of a scraping operation."""
    audit_logger = get_audit_logger('scraper')
    context = {'sport': sport}
    if year:
        context['year'] = year
    if set_name:
        context['set_name'] = set_name
    
    return audit_logger.log_operation('SCRAPING_START', status='STARTED', context=context, **kwargs)

def log_scraping_complete(sport: str, year: str = None, set_name: str = None, 
                         items_found: int = 0, **kwargs):
    """Log the completion of a scraping operation."""
    audit_logger = get_audit_logger('scraper')
    context = {
        'sport': sport,
        'items_found': items_found
    }
    if year:
        context['year'] = year
    if set_name:
        context['set_name'] = set_name
    
    return audit_logger.log_operation('SCRAPING_COMPLETE', status='SUCCESS', context=context, **kwargs)

def log_database_operation(operation: str, table: str, record_count: int = 0, **kwargs):
    """Log database operations."""
    audit_logger = get_audit_logger('database')
    context = {
        'table': table,
        'record_count': record_count
    }
    
    return audit_logger.log_operation(operation, status='SUCCESS', context=context, **kwargs)

def log_error(error: Exception, component: str = None, operation: str = None, **kwargs):
    """Log an error with comprehensive context."""
    audit_logger = get_audit_logger(component)
    return audit_logger.log_error_with_context(
        f"Error in {component or 'unknown'} component",
        error,
        operation=operation,
        context=kwargs
    )

# Performance monitoring utilities

class PerformanceMonitor:
    """Utility class for monitoring operation performance."""
    
    def __init__(self, operation: str, component: str = None):
        self.operation = operation
        self.component = component
        self.start_time = time.time()
        self.audit_logger = get_audit_logger(component)
    
    def __enter__(self):
        self.audit_logger.log_operation(self.operation, status='STARTED')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is None:
            # Success
            self.audit_logger.log_performance(self.operation, execution_time_ms, status='SUCCESS')
        else:
            # Error occurred
            self.audit_logger.log_error_with_context(
                f"Operation {self.operation} failed",
                exc_val,
                operation=self.operation
            )
    
    def checkpoint(self, checkpoint_name: str, **context):
        """Log a checkpoint during long-running operations."""
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        self.audit_logger.info(f"Checkpoint: {checkpoint_name}", 
                              operation=self.operation,
                              context={'checkpoint': checkpoint_name, 'elapsed_ms': elapsed_ms, **context})

# Cleanup function for application shutdown
def cleanup_audit_logging():
    """Clean up audit logging resources."""
    global _global_audit_logger
    if _global_audit_logger:
        _global_audit_logger.close()
        _global_audit_logger = None

# Register cleanup on module unload
import atexit
atexit.register(cleanup_audit_logging)
