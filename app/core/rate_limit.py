import threading
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from app.core.config import settings
from app.models import UserTier


lock = threading.Lock()
usage_cache = {}


def _get_cache_key(user_id: str, action: str, period: str) -> str:
    """Generate cache key for rate limit tracking."""
    return f"{user_id}:{action}:{period}"


def _get_reset_time(period: str) -> datetime:
    """Calculate reset time based on period."""
    now = datetime.utcnow()
    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif period == "month":
        if now.month == 12:
            return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return now


def check_rate_limit(action: str, period: str, limit: int, user_tier: UserTier):
    """
    Decorator to check rate limits for an action.

    Args:
        action: "upload" or "download"
        period: "day" or "month"
        limit: max requests allowed
        user_tier: free or premium
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract user_id from kwargs (passed by FastAPI dependency injection)
            user_id = kwargs.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User ID not found"
                )

            cache_key = _get_cache_key(user_id, action, period)

            with lock:
                now = datetime.utcnow()
                reset_time = _get_reset_time(period)

                # Initialize or get existing record
                if cache_key not in usage_cache:
                    usage_cache[cache_key] = {"count": 0, "reset_at": reset_time}

                record = usage_cache[cache_key]

                # Reset counter if period expired
                if now >= record["reset_at"]:
                    record["count"] = 0
                    record["reset_at"] = _get_reset_time(period)

                # Check limit
                if record["count"] >= limit:
                    reset_str = record["reset_at"].isoformat()
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Resets at {reset_str}"
                    )

                # Increment counter
                record["count"] += 1

            # Call the actual endpoint
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract user_id from kwargs
            user_id = kwargs.get("user_id")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User ID not found"
                )

            cache_key = _get_cache_key(user_id, action, period)

            with lock:
                now = datetime.utcnow()
                reset_time = _get_reset_time(period)

                # Initialize or get existing record
                if cache_key not in usage_cache:
                    usage_cache[cache_key] = {"count": 0, "reset_at": reset_time}

                record = usage_cache[cache_key]

                # Reset counter if period expired
                if now >= record["reset_at"]:
                    record["count"] = 0
                    record["reset_at"] = _get_reset_time(period)

                # Check limit
                if record["count"] >= limit:
                    reset_str = record["reset_at"].isoformat()
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Resets at {reset_str}"
                    )

                # Increment counter
                record["count"] += 1

            # Call the actual endpoint
            return func(*args, **kwargs)

        # Return async or sync wrapper based on function type
        if hasattr(func, "__await__"):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_user_rate_limit(user_tier: UserTier, action: str) -> tuple[int, str]:
    """
    Get rate limit for a user based on tier and action.

    Returns: (limit, period)
    """
    if user_tier == UserTier.PREMIUM:
        if action == "upload":
            return settings.PREMIUM_TIER_UPLOADS_PER_MONTH, "month"
        elif action == "download":
            return float("inf"), "day"
    else:  # FREE tier
        if action == "upload":
            return settings.FREE_TIER_UPLOADS_PER_DAY, "day"
        elif action == "download":
            return settings.FREE_TIER_DOWNLOADS_PER_DAY, "day"

    return float("inf"), "day"


def clear_user_cache(user_id: str):
    """Clear all cache entries for a user (useful for testing)."""
    with lock:
        keys_to_delete = [k for k in usage_cache.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_delete:
            del usage_cache[key]
