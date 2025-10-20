"""
Example: Single Image Prediction
Demonstrates how to make a single prediction request to the API.
"""

import mimetypes
import os
from pathlib import Path
from typing import List, Tuple, BinaryIO

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")


def predict_single_image(
    image_path: str, api_key: str, api_url: str = "http://localhost:8000"
) -> dict:
    """Make a single prediction request."""
    url = f"{api_url}/api/v1/predict"
    headers = {"accept": "application/json", "X-API-Key": api_key}
    with open(image_path, "rb") as f:
        files: List[Tuple[str, Tuple[str, BinaryIO, str]]] = [
            ("file", (Path(image_path).name, f, mimetypes.guess_type(image_path)[0] or ""))
        ]
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    if api_key is not None:
        result = predict_single_image("img/test_xray.png", api_key)
        print(f"Prediction: {result['prediction_class']}")
        print(f"Confidence: {result['confidence_score']:.2%}")
    else:
        print("API_KEY not found in environment variables")