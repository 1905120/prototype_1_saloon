"""
Utility functions
"""
from typing import Dict, Any, List
import re
from datetime import datetime

def parse_normal_time(text: str) -> str:
    text = text.strip().lower()

    # Add space before am/pm if missing
    text = re.sub(r"(am|pm)$", r" \1", text)

    # Extract number (H or H.MM) and am/pm
    text = text.replace(":", ".")
    m = re.match(r"^(\d{1,2}(?:\.\d{1,2})?)\s*(am|pm)$", text)
    #m = re.match(r"^(\d{1,2}(?::\d{2})?(?:\.\d{1,2})?)\s*(am|pm)$", text)
    if not m:
        return None
    
    num, meridiem = m.groups()

    # If it has a decimal -> treat as hours.minutes
    if "." in num:
        hours, minutes = num.split(".")
        hours = int(hours)
        minutes = int(minutes)

        # Minutes cannot exceed 59
        if minutes > 59:
            return None
    else:
        # No minutes: treat as full hour
        hours = int(num)
        minutes = 0

    # Validate hour range for 12-hour clock
    if hours < 1 or hours > 12:
        return None

    # Build normalized string
    normalized = f"{hours:02d}:{minutes:02d} {meridiem.upper()}"
    return normalized

def get_current_normal_time():
    return datetime.now().strftime("%I:%M %p")


def check_normal_time(t: str) -> datetime:
    """
    Convert normal time formats (2 pm, 2.30 am, 2:45 PM, etc.) into a datetime object.
    """
    t = t.lower().strip().replace('.', ':')      # convert 2.30 -> 2:30
    if "am" not in t and "pm" not in t:
        raise ValueError("Time must include AM/PM")
    
    # Ensure space before am/pm (ex: '2pm' -> '2 pm')
    t = t.replace("am", " am").replace("pm", " pm")
    
    # Add minutes if missing
    if ":" not in t:
        parts = t.split()
        hour = parts[0]
        t = f"{hour}:00 {parts[1]}"
    
    return datetime.strptime(t, "%I:%M %p")

def is_request_time_less(request_time: str, slot_time: str) -> bool:
    """
    Returns True if request_time < slot_time.
    """
    req = check_normal_time(request_time)
    slot = check_normal_time(slot_time)

    return req < slot