""" 
Example: Batch of asynchronous Predictions
Demonstrates how to make batch predictions using asynchronous HTTP requests.
"""
import asyncio
import aiohttp
from typing import List
from pathlib import Path


async def predict_batch_image_async(image_list: List[str], api_key: str, api_url: str = "http://localhost:8000"):
    """Make batch image predictions using asynchronous HTTP requests"""
    url = f"{api_url}/api/v1/predict/batch"
    headers = { 
        "accept": "application/json",
        "X-API-Key": api_key  # It will be set later
    }
    form_data = aiohttp.FormData()
    for image_path in image_list:
        form_data.add_field(
            "files", open(image_path, "rb"), 
            filename=Path(image_path).name, 
            content_type=f"image/{image_path.split('.')[-1]}"
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=form_data) as response:
            response_json = await response.json()
            response.raise_for_status()
            return response_json

if __name__ == "__main__":
    image_list = [
        "img/test_xray.png",
        "img/test_xray_copy.png",
    ]
    result = asyncio.run(predict_batch_image_async(image_list, "your-secret-api-key"))
    for i, prediction in enumerate(result["predictions"]):
        print(f"Image {i+1}:")
        print(f"Prediction: {prediction['prediction_class']}")
        print(f"Confidence: {prediction['confidence_score']:.2%}")
