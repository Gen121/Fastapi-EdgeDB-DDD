# pylint: disable=attribute-defined-outside-init
import edgedb
from fastapi import Depends

from allocation.dbschema.config import get_edgedb_client
from allocation.repositories import repository


class EdgedbUnitOfWork():
    batches: repository.EdgeDBRepository

    def __init__(self, async_client) -> None:
        self.async_client: edgedb.AsyncIOClient = async_client

    async def __aenter__(self) -> None:
        async for tx in self.async_client.transaction():
            self.transaction = tx
            break
        self.batches = repository.EdgeDBRepository(self.transaction)
        await self.transaction.__aenter__()

    async def __aexit__(self, extype, ex, tb) -> None:
        await self.transaction.__aexit__(extype, ex, tb)


async def get_uow(
    async_client_db: edgedb.AsyncIOClient = Depends(get_edgedb_client)
) -> EdgedbUnitOfWork:
    return EdgedbUnitOfWork(async_client_db)
