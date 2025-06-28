# File: utils/json_helpers.py
from datetime import date

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, date):
        return obj.isoformat() # Convert date to 'YYYY-MM-DD' string
    raise TypeError (f"Object of type {obj.__class__.__name__} is not JSON serializable")