import os
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_limiter_storage_url():
    return os.getenv("REDIS_URL", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_limiter_storage_url(),
    default_limits=["200/hour"]
)