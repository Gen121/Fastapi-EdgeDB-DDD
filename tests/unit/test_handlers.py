from datetime import date

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

    async def _get_by_batchref(self, batchref) -> model.Product | None:
        product = next((p for p in self._products if batchref in (b.reference for b in p.batches)), None)
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


class TestChangeBatchQuantity:
    async def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        await messagebus.handle(
            events.BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        product = await uow.products.get(sku="ADORABLE-SETTEE")
        [batch] = product.batches
        assert batch.available_quantity == 100

        await messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)

        assert batch.available_quantity == 50

    async def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            await messagebus.handle(e, uow)
        product = await uow.products.get(sku="INDIFFERENT-TABLE")
        [batch1, batch2] = product.batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        await messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
