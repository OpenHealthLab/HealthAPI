#!/usr/bin/env python3
"""
Script to create GitHub issues from GITHUB_ISSUES.md
Requires: pip install PyGithub python-dotenv
Usage: python scripts/create_github_issues.py
"""

import os
import re
from pathlib import Path
from github import Github
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "OpenHealthLab/HealthAPI"  # Update with your repo

# Issue data structure
issues_data = {
    "good_first_issues": [
        {
            "title": "Add example Python scripts for common API use cases",
            "body": """Create practical example scripts that demonstrate common usage patterns of the Healthcare AI Backend API. This will help users get started quickly and understand best practices.

## Goal
Provide ready-to-use examples that users can copy and modify for their needs.

## Steps to Complete
1. Create a new `examples/` directory in the project root
2. Create `examples/single_prediction.py` - Basic single image prediction
3. Create `examples/batch_prediction.py` - Batch prediction workflow
4. Create `examples/async_predictions.py` - Async usage with aiohttp
5. Create `examples/README.md` - Documentation for the examples
6. Update main README.md to link to examples

## Technical Details

**Files to create:**
- `examples/single_prediction.py`
- `examples/batch_prediction.py`
- `examples/async_predictions.py`
- `examples/README.md`

**Example implementation:**
```python
# examples/single_prediction.py
\"\"\"
Example: Single Image Prediction
Demonstrates how to make a single prediction request to the API.
\"\"\"
import requests
from pathlib import Path

def predict_single_image(image_path: str, api_key: str, api_url: str = "http://localhost:8000"):
    \"\"\"Make a single prediction request.\"\"\"
    url = f"{api_url}/api/v1/predict"
    headers = {"X-API-Key": api_key}
    
    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)
    
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = predict_single_image("test_xray.png", "your-api-key")
    print(f"Prediction: {result['prediction_class']}")
    print(f"Confidence: {result['confidence_score']:.2%}")
```

## Acceptance Criteria
- [ ] `examples/` directory created
- [ ] At least 3 different example scripts
- [ ] Each script includes detailed comments
- [ ] Examples handle errors gracefully
- [ ] README.md in examples directory explains each script
- [ ] Main README.md updated with link to examples
- [ ] All examples tested and working

## Getting Started
1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Comment on this issue to claim it
3. Fork the repository
4. Create examples with proper documentation
5. Test all examples
6. Submit PR with your changes

**Estimated Time:** 1-2 hours  
**Difficulty:** Beginner  
**Skills Required:** Python basics, REST API understanding
""",
            "labels": ["good first issue", "documentation", "help wanted"]
        },
        # Add more issues here...
    ],
    "intermediate_issues": [
        # Intermediate issues...
    ],
    "advanced_issues": [
        # Advanced issues...
    ]
}


def create_labels(repo):
    """Create necessary labels if they don't exist."""
    labels_config = [
        # Difficulty
        {"name": "good first issue", "color": "7057ff", "description": "Good for newcomers"},
        {"name": "intermediate", "color": "fbca04", "description": "Moderate difficulty"},
        {"name": "advanced", "color": "d93f0b", "description": "Complex task"},
        
        # Type
        {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
        {"name": "enhancement", "color": "a2eeef", "description": "New feature or request"},
        {"name": "documentation", "color": "0075ca", "description": "Improvements or additions to documentation"},
        {"name": "testing", "color": "00ffff", "description": "Test-related tasks"},
        {"name": "refactor", "color": "d4c5f9", "description": "Code refactoring"},
        {"name": "performance", "color": "ff6b6b", "description": "Performance improvements"},
        {"name": "security", "color": "ee0701", "description": "Security-related issues"},
        {"name": "devops", "color": "006b75", "description": "DevOps, CI/CD, deployment"},
        
        # Area
        {"name": "area: api", "color": "c2e0c6", "description": "API layer"},
        {"name": "area: ml", "color": "bfdadc", "description": "Machine learning"},
        {"name": "area: database", "color": "d4a5a5", "description": "Database related"},
        {"name": "area: devops", "color": "0e8a16", "description": "DevOps related"},
        
        # Status
        {"name": "help wanted", "color": "008672", "description": "Extra attention is needed"},
    ]
    
    existing_labels = {label.name for label in repo.get_labels()}
    
    for label_config in labels_config:
        if label_config["name"] not in existing_labels:
            try:
                repo.create_label(**label_config)
                print(f"✓ Created label: {label_config['name']}")
            except Exception as e:
                print(f"✗ Failed to create label {label_config['name']}: {e}")
        else:
            print(f"- Label already exists: {label_config['name']}")


def create_issues_from_data(repo, issues_data):
    """Create issues from the issues_data structure."""
    created_count = 0
    
    for category, issues in issues_data.items():
        print(f"\nCreating {category}...")
        for issue_data in issues:
            try:
                issue = repo.create_issue(
                    title=issue_data["title"],
                    body=issue_data["body"],
                    labels=issue_data["labels"]
                )
                print(f"✓ Created issue #{issue.number}: {issue.title}")
                created_count += 1
            except Exception as e:
                print(f"✗ Failed to create issue '{issue_data['title']}': {e}")
    
    return created_count


def main():
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not found in environment variables")
        print("Please create a GitHub personal access token and set it in .env file")
        print("Token needs 'repo' scope to create issues")
        return
    
    # Initialize GitHub client
    g = Github(GITHUB_TOKEN)
    
    try:
        repo = g.get_repo(REPO_NAME)
        print(f"Connected to repository: {repo.full_name}\n")
        
        # Create labels
        print("Setting up labels...")
        create_labels(repo)
        
        # Create issues
        print("\nCreating issues...")
        created = create_issues_from_data(repo, issues_data)
        
        print(f"\n{'='*50}")
        print(f"✓ Successfully created {created} issues!")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
