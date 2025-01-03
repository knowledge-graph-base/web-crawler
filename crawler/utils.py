# crawler/utils.py

import os
from datetime import datetime

def clean_filename(url):
    """Convert a URL into a safe filename by removing special chars."""
    return url.replace("http://", "").replace("https://", "").replace("/", "_")

def timestamp_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# crawler/utils.py (or define in main.py)
def manual_decision_prompt(message):
    """
    Simulate AI by asking the user for input.
    Replace with real AI calls in the future.
    """
    print("\n" + "="*50)
    print(f"AI Decision Needed: {message}")
    print("Options:")
    print("- 'yes' to proceed")
    print("- 'no' to skip")
    print("- 'skip' to skip this element")
    print("- For form inputs, enter the value or 'skip' to skip")
    print("="*50)
    
    choice = input("Your decision: ").strip()
    return choice
