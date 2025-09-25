import hashlib
import json
from functools import wraps
from typing import Callable
from fastapi import Request, Response

from app.cache import app_cache


def etag_support(cache_key: str, ttl_seconds: int = 3600):
    """
    Decorator to add ETag support to FastAPI endpoints.
    Args:
        cache_key (str): ETag cache key.
        ttl_seconds (int): TTL seconds.
    Usage:
        @router.get("/endpoint")
        @etag_support("endpoint")
        async def get_data(request: Request, response: Response):
            return {"data": "value"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            response: Response = kwargs.get("response")

            # check cache
            if cached := app_cache.get(cache_key):
                # check if client has current version
                if request:
                    # if if-none-match is in request, and it's value matches our etag
                    if request.headers.get("if-none-match", None) == cached.etag:
                        return Response(status_code=304, headers={"ETag": cached.etag})

                    # invariant - our cache does not match what user has, send new data
                    if response:
                        response.headers["ETag"] = f"{cached.etag}"
                    return None

            # cache miss - call function
            result = await func(*args, **kwargs)

            # gen etag for new response
            content_str = json.dumps(result, sort_keys=True, default=str)
            etag = hashlib.md5(content_str.encode()).hexdigest()

            # check if client already has this version (but we didn't have it cached
            if_none_match = None
            if request:
                if_none_match = request.headers.get("if-none-match", "").strip('"')

            # user has this etag, cache and respond
            if if_none_match and if_none_match == etag:
                app_cache.set(cache_key, result, etag, ttl_seconds)
                return Response(status_code=304, headers={"ETag": f"{etag}"})

            # invariant - user doesn't have this etag. cache it.
            app_cache.set(cache_key, etag, ttl_seconds)
            if response:
                response.headers["ETag"] = f"{etag}"
            return result

        return wrapper

    return decorator
