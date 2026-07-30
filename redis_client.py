from redis import Redis
from functools import lru_cache
import json
from typing import Any

@lru_cache
def get_redis() -> Redis:
    return Redis(host="redis", port=6379, db=0, decode_responses=True)

class RedisCache:
    def __init__(self):
        self.client = get_redis()

    def get(self, key:str):
        value=self.client.get(key)
        return json.loads(value) if value else None

    def set(self,key:str,value:Any,ttl:int=3600):
        self.client.setex(key, ttl, json.dumps(value))

    def delete(self,key:str):
        self.client.delete(key)

cache = RedisCache()
