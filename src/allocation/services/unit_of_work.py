# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc

import edgedb
from fastapi import Depends

from allocation.dbschema.config import get_edgedb_client
from allocation.repositories import repository
from allocation.services import messagebus


def email_sender(cls):
    orig_commit = cls.commit

    async def commit(self):
        for product in self.products.seen:
            for event in product.events:
                messagebus.handle(event)
        return await orig_commit(self)
    cls.commit = commit
    return cls


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository

    @abc.abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def __aexit__(self, extype, ex, tb):
        raise NotImplementedError

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError


@email_sender
class EdgedbUnitOfWork(AbstractUnitOfWork):
    products: repository.EdgeDBRepository

    def __init__(self, async_client) -> None:
        self.async_client: edgedb.AsyncIOClient = async_client

    async def __aenter__(self) -> None:
        async for tx in self.async_client.transaction():
            self.transaction = tx
            break
        self.products = repository.EdgeDBRepository(self.transaction)
        await self.transaction.__aenter__()

    async def __aexit__(self, extype, ex, tb) -> bool | None:
        try:
            await self.transaction.__aexit__(Exception, Exception(), tb)
        except (edgedb.errors.InternalClientError, edgedb.errors.InterfaceError):
            await self.async_client.aclose()
            return True
        # except repository.SynchronousUpdateError:
        #     await self.async_client.aclose()
        #     return False
        await self.async_client.aclose()
        return None

    async def commit(self):
        return await self.transaction.__aexit__(None, None, None)


async def get_uow(
    async_client_db: edgedb.AsyncIOClient = Depends(get_edgedb_client)
) -> EdgedbUnitOfWork:
    return EdgedbUnitOfWork(async_client_db)
