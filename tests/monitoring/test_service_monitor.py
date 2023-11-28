import asyncio
import unittest

import pytest

from monitoring.service_monitor import (
    SlidingWindowRateLimiter,
    OnDemandLeakyBucketRateLimiter,
    ServiceMonitor,
    get_rate_limiter_for,
)


class TestOnDemandLeakyBucketRateLimiter(unittest.IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        rate_limit = 2
        window_size = 1
        limiter = OnDemandLeakyBucketRateLimiter(rate_limit, window_size)

        # Acquire tokens within the rate limit
        for i in range(rate_limit):
            # await asyncio.sleep(window_size / rate_limit)
            result = await limiter.acquire()
            self.assertTrue(result, "Should acquire token within rate limit")

        # Acquire token beyond the rate limit
        result = await limiter.acquire()
        self.assertFalse(result, "Should not acquire token beyond rate limit")

        # Wait for the window to rest completely
        await asyncio.sleep(window_size)

        # Acquire token after the window reset
        result = await limiter.acquire()
        self.assertTrue(result, "Should acquire token after window reset")


class TestSlidingWindowRateLimiter(unittest.IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        rate_limit = 2
        window_size = 1
        limiter = SlidingWindowRateLimiter(rate_limit, window_size)

        # Acquire tokens within the rate limit
        for i in range(rate_limit):
            # await asyncio.sleep(window_size / rate_limit)
            result = await limiter.acquire()
            self.assertTrue(result, "Should acquire token within rate limit")

        # Acquire token beyond the rate limit
        result = await limiter.acquire()
        self.assertFalse(result, "Should not acquire token beyond rate limit")

        # Wait for the window to rest completely
        await asyncio.sleep(window_size)

        # Acquire token after the window reset
        result = await limiter.acquire()
        self.assertTrue(result, "Should acquire token after window reset")

    @pytest.mark.asyncio
    async def test_refill(self):
        rate_limit = 2
        window_size = 1
        limiter = SlidingWindowRateLimiter(rate_limit, window_size)
        self.assertEqual(limiter.tokens, rate_limit)

        # Set last_refill_time to simulate a past refill
        limiter.last_refill_time = asyncio.get_event_loop().time() - window_size

        # Refill tokens
        await limiter.slide()

        # Ensure tokens are refilled
        self.assertAlmostEqual(limiter.tokens, rate_limit)


class TestServiceMonitor(unittest.IsolatedAsyncioTestCase):
    @pytest.mark.asyncio
    async def test_process_fails_after_limit(self):
        monitor = ServiceMonitor()
        monitor.register_code_for_url(
            "foo",
            429,
            get_rate_limiter_for("strict", 2, 1)
        )
        await monitor.process("foo", 429)
        await monitor.process("foo", 429)
        with self.assertRaises(ValueError) as ctx:
            await monitor.process("foo", 429)
        self.assertIn("Allowed limit (2)", str(ctx.exception))
