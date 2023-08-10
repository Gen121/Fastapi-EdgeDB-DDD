from datetime import date

import pytest

import allocation.repositories.repository as repository
from allocation.adapters import email
from allocation.domain import commands, events, model
from allocation.services import handlers, unit_of_work
from allocation.services.messagebus import get_messagebus


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


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published: list[events.Event] = []

    async def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield self.events_published.append(product.events.pop(0))


class TestAddBatch:
    async def test_add_batch(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("b1", "CRUNCHY-ARMCHAIR", 100, None),
        )
        assert await uow.products.get(sku="CRUNCHY-ARMCHAIR") is not None
        assert uow.committed

    async def test_add_batch_for_existing_product(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("b1", "GARISH-RUG", 100, None),
        )
        await messagebus.handle(
            commands.CreateBatch("b2", "GARISH-RUG", 99, None),
        )
        product = await uow.products.get("GARISH-RUG")
        assert "b2" in [b.reference for b in product.batches]


class TestAllocate:
    async def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("batch1", "COMPLICATED-LAMP", 100, None),
        )
        result = await messagebus.handle(
            commands.Allocate("o1", "COMPLICATED-LAMP", 10),
        )
        assert result[0] == "batch1"

    async def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("b1", "AREALSKU", 100, None),
        )
        try:
            await messagebus.handle(
                commands.Allocate("o1", "NONEXISTENTSKU", 10),
            )
        except handlers.InvalidSku as e:
            with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
                raise e

    async def test_sends_email_on_out_of_stock_error(self, monkeypatch):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None),
        )

        async def mock_send_mail(to, subject):
            assert to == "stock@made.com"
            assert subject == "Out of stock for POPULAR-CURTAINS"

        monkeypatch.setattr(email, "send", mock_send_mail)

        await messagebus.handle(
            commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None),
        )
        await messagebus.handle(
            commands.Allocate("o1", "POPULAR-CURTAINS", 10),
        )


class TestChangeBatchQuantity:
    async def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        await messagebus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None),
        )
        product = await uow.products.get(sku="ADORABLE-SETTEE")
        [batch] = product.batches
        assert batch.available_quantity == 100

        await messagebus.handle(
            commands.ChangeBatchQuantity("batch1", 50),
        )

        assert batch.available_quantity == 50

    async def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        messagebus = await get_messagebus(uow)
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            await messagebus.handle(
                e,
            )
        product = await uow.products.get(sku="INDIFFERENT-TABLE")
        [batch1, batch2] = product.batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        await messagebus.handle(
            commands.ChangeBatchQuantity("batch1", 25),
        )

        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30

    async def test_reallocates_if_necessary_isolated(self):
        uow = FakeUnitOfWorkWithFakeMessageBus()
        messagebus = await get_messagebus(uow)

        # test setup as before
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            await messagebus.handle(e)
        product = await uow.products.get(sku="INDIFFERENT-TABLE")
        [batch1, batch2] = product.batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        await messagebus.handle(commands.ChangeBatchQuantity("batch1", 25))

        # assert on new events emitted rather than downstream side-effects
        *_, reallocation_event = uow.events_published
        assert isinstance(reallocation_event, commands.Allocate)
        assert reallocation_event.orderid in {"order1", "order2"}
        assert reallocation_event.sku == "INDIFFERENT-TABLE"
