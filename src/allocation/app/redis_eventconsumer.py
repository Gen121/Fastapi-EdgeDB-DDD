import asyncio
import json
import logging
import redis.asyncio as redis

import edgedb

from allocation.app.settings import settings
from allocation.domain import commands
from allocation.services import unit_of_work
from allocation.services.messagebus import get_messagebus


logger = logging.getLogger(__name__)

r = redis.from_url(settings.get_redis_url())


async def get_async_client_db(test_db: bool = False):
    client = edgedb.create_async_client(
        settings.get_edgedb_dsn(test_db=test_db), tls_security="insecure"
    )
    await client.ensure_connected()
    return client


async def get_uow(async_client_db: edgedb.AsyncIOClient) -> unit_of_work.EdgedbUnitOfWork:
    return unit_of_work.EdgedbUnitOfWork(async_client_db)


async def main():
    client = await get_async_client_db()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe("change_batch_quantity")

    async for m in pubsub.listen():
        try:
            await handle_change_batch_quantity(m, client)
        except Exception:
            await client.aclose()
            break


async def handle_change_batch_quantity(m, client):
    uow = await get_uow(client)
    logging.debug("handling %s", m)
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus = await get_messagebus(uow)
    await messagebus.handle(cmd)


if __name__ == "__main__":
    asyncio.run(main())
