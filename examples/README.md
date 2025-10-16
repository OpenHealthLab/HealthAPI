# HealthAPI Examples

This directory contains example scripts demonstrating how to use the HealthAPI for making prediction requests.

## Files

- [single_prediction.py](file:single_prediction.py) - Example of making a single image prediction request
- [batch_prediction.py](file:batch_prediction.py) - Example of making batch image predictions using synchronous HTTP requests
- [async_predictions.py](file:async_predictions.py) - Example of making batch image predictions using asynchronous HTTP requests

## Usage

Each script demonstrates different ways to interact with the HealthAPI:

1. **Single Prediction**: Sends one image file to the API and receives a prediction result
2. **Batch Prediction**: Sends multiple image files in a single request synchronously
3. **Async Batch Prediction**: Sends multiple image files in a single request asynchronously

All examples require:
- An API key (replace `"your-secret-api-key"` with your actual API key)
- The HealthAPI service running at `http://localhost:8000` (or update the `api_url` parameter)
- Image files located in the `img/` directory

## Requirements

- Python 3.7+
- `requests` library for synchronous examples
- `aiohttp` library for asynchronous examples
- `pathlib` (standard library)