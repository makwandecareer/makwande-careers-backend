import logging, time
from functools import wraps
from prometheus_client import Counter, Histogram

REQUESTS=Counter("http_requests_total","Total HTTP requests",["endpoint"])
LATENCY=Histogram("http_request_duration_seconds","Request latency",["endpoint"])

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger("makwande")

def monitor(endpoint:str):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**k):
            start=time.perf_counter()
            try:
                return fn(*a,**k)
            finally:
                REQUESTS.labels(endpoint=endpoint).inc()
                LATENCY.labels(endpoint=endpoint).observe(time.perf_counter()-start)
                logger.info("%s completed",endpoint)
        return wrapper
    return deco
