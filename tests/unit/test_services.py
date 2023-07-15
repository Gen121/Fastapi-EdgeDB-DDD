from contextlib import AbstractAsyncContextManager

import pytest

import allocation.domain.model as model
import allocation.repositories.repository as repository
import allocation.services.batch_services as batch_services


class FakeRepository(repository.AbstractRepository):
    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeRepository([model.Batch(ref, sku, qty, eta), ])

    def __init__(self, batches):
        self._batches = set(batches)

    async def add(self, batch):
        self._batches.add(batch)

    async def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    async def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork():
    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, ty, val, tb):
        await self.rollback()

    async def commit(self):
        self.session = True

    async def rollback(self):
        pass


async def test_add_batch():
    uow = FakeUnitOfWork()
    await batch_services.add_batch(uow, "b1", "CRUNCHY-ARMCHAIR", 100, None, set())
    assert await uow.batches.get(reference="b1") is not None


async def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    await batch_services.add_batch(
        uow=uow, reference="batch1", sku="COMPLICATED-LAMP",
        purchased_quantity=100, eta=None, allocations=set()
    )
    result = await batch_services.allocate(uow=uow, orderid="o1", sku="COMPLICATED-LAMP", qty=10)
    assert result == "batch1"


async def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    await batch_services.add_batch(
        uow=uow, reference="b1", sku="AREALSKU",
        purchased_quantity=100, eta=None, allocations=set()
    )
    try:
        await batch_services.allocate(uow=uow, orderid="o1", sku="NONEXISTENTSKU", qty=10)
    except batch_services.InvalidSku as e:
        with pytest.raises(batch_services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e
