import json
import logging
from dataclasses import asdict

import redis.asyncio as redis

from allocation.app.settings import settings
from allocation.domain import events

logger = logging.getLogger(__name__)

r = redis.from_url(settings.get_redis_url())


async def publish(channel, event: events.Event):
    logging.debug(f"publishing: channel={channel}, event={event}")
    await r.publish(channel, json.dumps(asdict(event)))
