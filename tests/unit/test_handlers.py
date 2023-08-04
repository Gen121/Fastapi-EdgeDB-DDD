import pytest

import allocation.repositories.repository as repository
from allocation.adapters import email
from allocation.domain import events, model
from allocation.services import handlers, messagebus, unit_of_work


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    async def _add(self, product: model.Product) -> None:
        self.seen.add(product)
        self._products.add(product)

    async def _get(self, sku) -> model.Product | None:
        product = next((p for p in self._products if p.sku == sku), None)
        return product


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, extype, ex, tb):
        await self.rollback()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class TestAddBatch:
    async def test_add_batch(self):
        uow = FakeUnitOfWork()
        await messagebus.handle(events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow)
        assert await uow.products.get(sku="CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    async def test_add_batch_for_existing_product(self):
        uow = FakeUnitOfWork()
        await messagebus.handle(events.BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        await messagebus.handle(events.BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        product = await uow.products.get("GARISH-RUG")
        assert "b2" in [b.reference for b in product.batches]


class TestAllocate:
    async def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        await messagebus.handle(events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow)
        result = await messagebus.handle(events.AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow)
        assert result[0] == "batch1"

    async def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        await messagebus.handle(events.BatchCreated("b1", "AREALSKU", 100, None), uow)
        try:
            await messagebus.handle(events.AllocationRequired("o1", "NONEXISTENTSKU", 10), uow)
        except handlers.InvalidSku as e:
            with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
                raise e

    async def test_sends_email_on_out_of_stock_error(self, monkeypatch):
        uow = FakeUnitOfWork()
        await messagebus.handle(events.BatchCreated("b1", "POPULAR-CURTAINS", 9, None), uow)

        async def mock_send_mail(to, subject):
            assert to == "stock@made.com"
            assert subject == "Out of stock for POPULAR-CURTAINS"

        monkeypatch.setattr(email, "send", mock_send_mail)

        await messagebus.handle(events.BatchCreated("b1", "POPULAR-CURTAINS", 9, None), uow)
        await messagebus.handle(events.AllocationRequired("o1", "POPULAR-CURTAINS", 10), uow)
