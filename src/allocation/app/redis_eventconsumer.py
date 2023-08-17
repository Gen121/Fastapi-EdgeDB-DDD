import asyncio
import json
import logging

import redis.asyncio as redis

from allocation.app.settings import settings
from allocation.bootstrap import bootstrap
from allocation.domain import commands

logger = logging.getLogger(__name__)

r = redis.from_url(settings.get_redis_url())


async def consumer_loop():
    messagebus = bootstrap.messagebus
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe("change_batch_quantity")

    async for m in pubsub.listen():
        await handle_change_batch_quantity(m, messagebus)


async def handle_change_batch_quantity(m, messagebus):
    logging.debug("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    await messagebus.handle(cmd)


if __name__ == "__main__":
    asyncio.run(consumer_loop())
