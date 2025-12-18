"""
Redirect to the main database manager
"""
import sys
import os

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the actual database manager
from database import db_manager, DatabaseManager

# Re-export everything
__all__ = ['db_manager', 'DatabaseManager']