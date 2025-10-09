"""
Core utility functions used across the application.
"""

from datetime import datetime, timedelta
from typing import Optional


def calculate_hours_difference(start_time: datetime, end_time: datetime) -> float:
    """
    Calculate the difference in hours between two datetime objects.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        
    Returns:
        float: Hours difference (e.g., 8.5 for 8 hours 30 minutes)
    """
    if not start_time or not end_time:
        return 0.0
    
    delta = end_time - start_time
    return delta.total_seconds() / 3600


def format_duration(hours: float) -> str:
    """
    Format hours as human-readable duration string.
    
    Args:
        hours: Number of hours (e.g., 8.5)
        
    Returns:
        str: Formatted string (e.g., "8h 30m")
    """
    if not hours:
        return "0h"
    
    full_hours = int(hours)
    minutes = int((hours - full_hours) * 60)
    
    if minutes > 0:
        return f"{full_hours}h {minutes}m"
    return f"{full_hours}h"


def generate_employee_id(prefix: str = "EMP") -> str:
    """
    Generate a unique employee ID.
    
    Args:
        prefix: Prefix for the ID (default: "EMP")
        
    Returns:
        str: Generated ID (e.g., "EMP-20250110-001")
    """
    from django.utils import timezone
    import random
    
    date_str = timezone.now().strftime("%Y%m%d")
    random_suffix = f"{random.randint(0, 999):03d}"
    
    return f"{prefix}-{date_str}-{random_suffix}"