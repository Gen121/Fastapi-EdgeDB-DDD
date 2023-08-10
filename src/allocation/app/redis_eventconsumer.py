import asyncio
import json
import logging
from fastapi import Depends
import redis.asyncio as redis

from allocation.app.settings import settings
from allocation.domain import commands
from allocation.services import unit_of_work
from allocation.services.messagebus import get_messagebus


logger = logging.getLogger(__name__)

r = redis.from_url(settings.get_redis_url())


async def main():
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe("change_batch_quantity")

    async for m in pubsub.listen():
        await handle_change_batch_quantity(m)


async def handle_change_batch_quantity(
    m, uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
):
    logging.debug("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus = await get_messagebus(uow)
    await messagebus.handle(cmd)


if __name__ == "__main__":
    asyncio.run(main())
