"""
Example: Batch of Image Predictions
Demonstrates how to make batch predictions request to the API.
"""
import requests
from pathlib import Path
from typing import List

def predict_batch_images(image_list: List[str], api_key: str, api_url: str = "http://localhost:8000"):
    """Make batch image predictions"""
    url = f"{api_url}/api/v1/predict/batch"
    headers = { 
        "accept": "application/json",
        "X-API-Key": api_key  # It will be set later
    }
    files = []
    for image_path in image_list:
        files.append(
            ("files", (Path(image_path).name, open(image_path, "rb"), f"image/{image_path.split('.')[-1]}"))
        )
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    image_list = [
        "img/test_xray.png",
        "img/test_xray_copy.png",
    ]
    result = predict_batch_images(image_list, "your-secret-api-key")
    for i, prediction in enumerate(result["predictions"]):
        print(f"Image {i+1}:")
        print(f"Prediction: {prediction['prediction_class']}")
        print(f"Confidence: {prediction['confidence_score']:.2%}")