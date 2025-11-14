from fastapi import HTTPException
from typing import Optional, Dict, Any
from loguru import logger


def create_error_response(
    error: Exception,
    user_message: str,
    status_code: int = 500,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    logger.error(f"{user_message}: {str(error)}")
    
    response_detail = {
        'success': False,
        'message': user_message,
        'error_code': error_code or f'ERR_{status_code}'
    }
    
    if details:
        response_detail['details'] = details
    
    return HTTPException(status_code=status_code, detail=response_detail)


def validation_error(message: str, field: Optional[str] = None) -> HTTPException:
    details = {'field': field} if field else None
    logger.warning(f"Validation error: {message}")
    
    return HTTPException(
        status_code=400,
        detail={
            'success': False,
            'message': message,
            'error_code': 'VALIDATION_ERROR',
            'details': details
        }
    )


def not_found_error(resource: str, identifier: Optional[str] = None) -> HTTPException:
    message = f"{resource} not found"
    if identifier:
        message += f": {identifier}"
    
    logger.warning(f"Not found: {message}")
    
    return HTTPException(
        status_code=404,
        detail={
            'success': False,
            'message': message,
            'error_code': 'NOT_FOUND'
        }
    )


def server_error(error: Exception, context: str) -> HTTPException:
    logger.error(f"Server error in {context}: {type(error).__name__}: {str(error)}")
    
    return HTTPException(
        status_code=500,
        detail={
            'success': False,
            'message': 'An internal server error occurred. Please try again later.',
            'error_code': 'INTERNAL_ERROR',
            'context': context
        }
    )


def database_error(error: Exception, operation: str) -> HTTPException:
    logger.error(f"Database error during {operation}: {type(error).__name__}: {str(error)}")
    
    return HTTPException(
        status_code=500,
        detail={
            'success': False,
            'message': f'Database operation failed: {operation}',
            'error_code': 'DATABASE_ERROR'
        }
    )
