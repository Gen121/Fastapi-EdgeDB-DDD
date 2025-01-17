# pylint: disable=attribute-defined-outside-init
from __future__ import annotations

import abc

import edgedb

from allocation.repositories import repository


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

    async def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)


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
        # TODO: implement Optimistic parallelism with version numbers
        # except repository.SynchronousUpdateError:
        #     await self.async_client.aclose()
        #     return False
        await self.async_client.aclose()
        return None

    async def commit(self):
        return await self.transaction.__aexit__(None, None, None)
