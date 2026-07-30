from app.cache.redis_client import cache

def get_cached_profile(user_id:str):
    key=f"profile:{user_id}"
    profile=cache.get(key)
    if profile:
        return profile

    profile={"user_id":user_id,"status":"loaded_from_database"}
    cache.set(key, profile, ttl=1800)
    return profile
