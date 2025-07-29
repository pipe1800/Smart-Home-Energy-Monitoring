import time
from collections import defaultdict
from fastapi import HTTPException, status

class RateLimiter:
    def __init__(self, max_attempts=5, window_minutes=15):
        self.max_attempts = max_attempts
        self.window_seconds = window_minutes * 60
        self.attempts = defaultdict(list)
    
    def check_rate_limit(self, identifier: str):
        """Check if the identifier has exceeded rate limits"""
        now = time.time()
        # Clean old attempts
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if now - attempt_time < self.window_seconds
        ]
        
        # Check if exceeded
        if len(self.attempts[identifier]) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Try again later."
            )
        
        # Record this attempt
        self.attempts[identifier].append(now)

# Global rate limiter instances
auth_rate_limiter = RateLimiter(max_attempts=5, window_minutes=15)
device_rate_limiter = RateLimiter(max_attempts=20, window_minutes=5)
ai_rate_limiter = RateLimiter(max_attempts=10, window_minutes=5)
