import asyncio
import enum
import logging
import math
import time

handler = logging.FileHandler('logfile.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(level="INFO")


class RateLimiter:
    def __init__(self, rate_limit=10, window_size=60):
        self.rate_limit = rate_limit
        self.window_size = window_size

    async def acquire(self):
        pass

    def make_api_request(self, endpoint, params):
        pass


class OnDemandLeakyBucketRateLimiter(RateLimiter):
    def __init__(self, rate_limit, window_size):
        super().__init__(rate_limit, window_size)
        self.bucket = asyncio.Queue(maxsize=rate_limit)
        self.lock = asyncio.Lock()

    async def _leak_token(self):
        async with self.lock:
            allowed = True
            try:
                if self.bucket.qsize() >= self.rate_limit:
                    _, entry_time = self.bucket.get_nowait()
                    allowed = (time.time() - entry_time > self.window_size)
            except asyncio.QueueEmpty:
                allowed = True
        return allowed

    async def acquire(self):
        allowed = await self._leak_token()
        if allowed:
            self.bucket.put_nowait((None, time.time()))
        return allowed


class SlidingWindowRateLimiter(RateLimiter):
    def __init__(self, rate_limit, window_size):
        super().__init__(rate_limit, window_size)
        self.tokens = rate_limit
        self.last_refill_time = asyncio.get_event_loop().time()

    async def slide(self):
        current_time = asyncio.get_event_loop().time()
        time_passed = current_time - self.last_refill_time
        new_tokens = math.floor(time_passed * (self.rate_limit / self.window_size))
        self.tokens = min(self.tokens + new_tokens, self.rate_limit)
        self.last_refill_time = current_time

    async def acquire(self):
        await self.slide()

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        else:
            return False


mode2rate_limiter_class = {
    "strict": OnDemandLeakyBucketRateLimiter,
    "bursty": SlidingWindowRateLimiter,
}


class StatusCodes(enum.Enum):
    proxy = 429
    application = 500
    ok = 200


code2error = {e.value: e for e in StatusCodes}


class RateError(Exception):
    def __init__(self, status_code: StatusCodes):
        self.status_code = status_code

    def __str__(self):
        return f"Fatal. Too many {self.status_code.name} errors"


def get_rate_limiter_for(mode, rate_limit, window_size):
    if mode not in mode2rate_limiter_class:
        raise ValueError(
            f"Rate limiter corresponding to {mode} has not been implemented, please use one of the available modes = "
            f"{set(mode2rate_limiter_class.keys())}"
        )
    return mode2rate_limiter_class[mode](rate_limit, window_size)


class StatusCodeLimiters:
    def __init__(self):
        self.status_code2rate_limiter: dict[int, RateLimiter] = {}

    def register_limiter_for_code(self, code: StatusCodes, rate_limiter: RateLimiter):
        # potentially could also check for existing limiter for given code to avoid overwriting
        self.status_code2rate_limiter[code.value] = rate_limiter

    def rate_limiter_for(self, status_code: StatusCodes):
        return self.status_code2rate_limiter.get(status_code.value)


class ServiceMonitor:
    def __init__(self):
        self.url2status_code_limiters: dict[str, StatusCodeLimiters] = {}

    def register_code_for_url(self, url, status_code: StatusCodes, rate_limiter: RateLimiter):
        if url not in self.url2status_code_limiters:
            self.url2status_code_limiters[url] = StatusCodeLimiters()
        status_code_limiters = self.url2status_code_limiters[url]
        status_code_limiters.register_limiter_for_code(status_code, rate_limiter)

    async def process(self, url, status_code: StatusCodes):
        logger.info(f"Request to {url} is being processed, status code = {status_code.value}")
        error_rate_limiters = self.url2status_code_limiters.get(url)
        if not error_rate_limiters:
            return

        rate_limiter = error_rate_limiters.rate_limiter_for(status_code)
        if not rate_limiter:
            return

        if not await rate_limiter.acquire():
            raise RateError(status_code)
