import asyncio
import random

import requests

from monitoring.service_monitor import ServiceMonitor, get_rate_limiter_for

service_monitor = ServiceMonitor()
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-1",
    code=429,
    rate_limiter=get_rate_limiter_for("bursty", rate_limit=10, window_size=60)
)
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-1",
    code=500,
    rate_limiter=get_rate_limiter_for("bursty", rate_limit=10, window_size=60)
)
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-2",
    code=429,
    rate_limiter=get_rate_limiter_for("strict", rate_limit=10, window_size=60)
)
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-2",
    code=500,
    rate_limiter=get_rate_limiter_for("strict", rate_limit=10, window_size=60)
)
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-3",
    code=429,
    rate_limiter=get_rate_limiter_for("strict", rate_limit=10, window_size=60)
)
service_monitor.register_code_for_url(
    url="http://0.0.0.0:8080/health-3",
    code=500,
    rate_limiter=get_rate_limiter_for("strict", rate_limit=10, window_size=60)
)


async def request_service(url):
    # Trigger monitoring here
    response = requests.get(url)
    await service_monitor.process(url, response.status_code)
    return response


async def sample_run():
    for _ in range(10000):
        endpoints = [
            "http://0.0.0.0:8080/health-1",
            "http://0.0.0.0:8080/health-2",
            "http://0.0.0.0:8080/health-3",
        ]
        endpoint = random.choice(endpoints)
        await asyncio.sleep(0.1)
        await request_service(endpoint)


if __name__ == "__main__":
    asyncio.run(sample_run())
