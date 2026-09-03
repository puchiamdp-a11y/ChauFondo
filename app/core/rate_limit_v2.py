import threading
from datetime import datetime, timedelta
from typing import Tuple, Optional
from app.core.config import settings

# In-memory cache: key -> (count, reset_time)
usage_cache = {}
cache_lock = threading.Lock()


def get_limit_for_tier(client_id: str, user_tier: Optional[str]) -> Tuple[int, str]:
    """
    Get upload limit and period for client.

    - Anonymous (IP): 50 uploads/day
    - Free tier (user_id): 5 uploads/day
    - Premium tier (user_id): Unlimited (return very high number)
    """
    if user_tier == "premium":
        return (1000, "month")  # Effectively unlimited
    elif user_tier == "free":
        return (5, "day")
    else:  # Anonymous
        return (50, "day")


def get_cache_key(client_id: str, user_tier: Optional[str], action: str = "upload") -> str:
    """Generate cache key for rate limit tracking."""
    limit, period = get_limit_for_tier(client_id, user_tier)

    if period == "day":
        date_key = datetime.utcnow().date().isoformat()
    else:  # month
        date_key = datetime.utcnow().strftime("%Y-%m")

    return f"{client_id}:{action}:{date_key}"


def check_rate_limit(client_id: str, user_tier: Optional[str], action: str = "upload") -> Tuple[bool, Optional[str]]:
    """
    Check if client has exceeded rate limit.

    Returns: (allowed: bool, error_message: Optional[str])
    """
    limit, period = get_limit_for_tier(client_id, user_tier)
    cache_key = get_cache_key(client_id, user_tier, action)

    with cache_lock:
        current_count, reset_time = usage_cache.get(cache_key, (0, None))

        if reset_time and datetime.utcnow() > reset_time:
            # Reset counter if period expired
            current_count = 0
            reset_time = None

        if current_count >= limit:
            # Calculate next reset time
            if not reset_time:
                if period == "day":
                    reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                else:  # month
                    reset_time = (datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1)

            seconds_until_reset = int((reset_time - datetime.utcnow()).total_seconds())
            tier_name = user_tier if user_tier else "anonymous"

            return False, f"Rate limit exceeded for {tier_name} tier. Resets in {seconds_until_reset} seconds."

        # Increment counter
        current_count += 1
        if not reset_time:
            if period == "day":
                reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:  # month
                reset_time = (datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1)

        usage_cache[cache_key] = (current_count, reset_time)

        return True, None


def clear_client_cache(client_id: str, action: str = "upload"):
    """Clear rate limit cache for a client (used for upgrades)."""
    with cache_lock:
        # Clear all cache entries for this client
        keys_to_delete = [k for k in usage_cache.keys() if k.startswith(f"{client_id}:{action}:")]
        for key in keys_to_delete:
            del usage_cache[key]
