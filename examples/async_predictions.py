"""
Example: Batch of asynchronous Predictions
Demonstrates how to make batch predictions using asynchronous HTTP requests.
"""

import asyncio
import mimetypes
import os
from pathlib import Path
from typing import Any, List

import aiohttp
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")


async def predict_batch_image_async(
    image_list: List[str], api_key: str, api_url: str = "http://localhost:8000"
) -> dict:
    """Make batch image predictions using asynchronous HTTP requests"""
    url = f"{api_url}/api/v1/predict/batch"
    headers = {"accept": "application/json", "X-API-Key": api_key}
    form_data = aiohttp.FormData()
    file_handles: List[Any] = []  # To collect opened file objects

    try:
        for image_path in image_list:
            file_handle = open(image_path, "rb")
            file_handles.append(file_handle)
            form_data.add_field(
                "files",
                file_handle,
                filename=Path(image_path).name,
                content_type=mimetypes.guess_type(image_path)[0],
            )

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form_data) as response:
                response.raise_for_status()
                response_json = await response.json()
                return response_json
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
        result = asyncio.run(predict_batch_image_async(image_list, api_key))
        for i, prediction in enumerate(result["predictions"]):
            print(f"Image {i+1}:")
            print(f"Prediction: {prediction['prediction_class']}")
            print(f"Confidence: {prediction['confidence_score']:.2%}")
    else:
        print("API_KEY not found in environment variables")
