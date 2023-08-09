import json
import redis.asyncio as redis

from allocation.app.settings import settings

REDIS_URL = settings.get_redis_uri()
r = redis.from_url(REDIS_URL)


async def subscribe_to(channel):
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    confirmation = await pubsub.get_message(timeout=3)
    assert confirmation is not None
    assert confirmation["type"] == "subscribe"
    return pubsub


async def publish_message(channel, message):
    await r.publish(channel, json.dumps(message))
