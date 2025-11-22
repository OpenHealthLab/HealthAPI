"""
Example: Batch of Image Predictions
Demonstrates how to make batch predictions request to the API.
"""

import mimetypes
import os
from pathlib import Path
from typing import List, Tuple, BinaryIO

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")


def predict_batch_images(
    image_list: List[str], api_key: str, api_url: str = "http://localhost:8000"
) -> dict:
    """Make batch image predictions"""
    url = f"{api_url}/api/v1/predict/batch"
    headers = {"accept": "application/json", "X-API-Key": api_key}
    files: List[Tuple[str, Tuple[str, BinaryIO, str]]] = []
    file_handles: List[BinaryIO] = []  # To collect opened file objects

    try:
        for image_path in image_list:
            f = open(image_path, "rb")
            file_handles.append(f)
            files.append(
                (
                    "files",
                    (
                        Path(image_path).name,
                        f,
                        mimetypes.guess_type(image_path)[0] or "",
                    ),
                )
            )

        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        raise exc
    finally:
        # Close all opened files
        for f in file_handles:
            f.close()


if __name__ == "__main__":
    if api_key is not None:
        image_list = [
            "img/test_xray.png",
            "img/test_xray_copy.png",
        ]
        result = predict_batch_images(image_list, api_key)
        for i, prediction in enumerate(result["predictions"]):
            print(f"Image {i+1}:")
            print(f"Prediction: {prediction['prediction_class']}")
            print(f"Confidence: {prediction['confidence_score']:.2%}")
    else:
        print("API_KEY not found in environment variables")