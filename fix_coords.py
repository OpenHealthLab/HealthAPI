#!/usr/bin/env python3
"""Script to normalize bbox coordinates in test file"""
import re

def normalize_coord(match):
    """Convert pixel coordinate to normalized (0-1) coordinate"""
    key = match.group(1)
    value = int(match.group(2))
    
    # Normalize by dividing by 1000 (assuming max image dimension ~1000px)
    normalized = value / 1000.0
    
    return f"{key}={normalized}"

# Read the file
with open('tests/test_detection_service.py', 'r') as f:
    content = f.read()

# Replace all bbox coordinates
pattern = r'(bbox_[xy][12])=(-?\d+)'
new_content = re.sub(pattern, normalize_coord, content)

# Write back
with open('tests/test_detection_service.py', 'w') as f:
    f.write(new_content)

print("Coordinates normalized!")
