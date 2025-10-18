"""
Example: Single Image Prediction
Demonstrates how to make a single prediction request to the API.
"""
import requests
from pathlib import Path

def predict_single_image(image_path: str, api_key: str, api_url: str = "http://localhost:8000"):
    """Make a single prediction request."""
    url = f"{api_url}/api/v1/predict"
    headers = {
        'accept': 'application/json',
        "X-API-Key": api_key # It will be set later
    }
    with open(image_path, "rb") as f:
        files=[
            ('file',(Path(image_path).name,f,f"image/{image_path.split('.')[-1]}"))
        ]
        response = requests.post(url, headers=headers, files=files)
    
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = predict_single_image("img/test_xray.png", "your-secret-api-key")
    print(f"Prediction: {result['prediction_class']}")
    print(f"Confidence: {result['confidence_score']:.2%}")