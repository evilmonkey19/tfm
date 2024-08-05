import redis
import os
import time

def connect_to_redis():
    retries = 5
    while retries > 0:
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            print("Connected to Redis")
            return r
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            retries -= 1
            time.sleep(5)
    raise Exception("Could not connect to Redis after several attempts")

redis_client = connect_to_redis()