from unittest import mock

import pytest

import allocation.domain.model as model
import allocation.repositories.repository as repository
import allocation.services.handlers as handlers
from allocation.services.unit_of_work import AbstractUnitOfWork, email_sender


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


@email_sender
class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, ty, val, tb):
        await self.rollback()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


async def test_add_batch():
    uow = FakeUnitOfWork()
    await handlers.add_batch(uow, "b1", "CRUNCHY-ARMCHAIR", 100, None, set())
    assert await uow.products.get(sku="CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


async def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    await handlers.add_batch(uow, "b1", "GARISH-RUG", 100, None, set())
    await handlers.add_batch(uow, "b2", "GARISH-RUG", 99, None, set())
    product = await uow.products.get("GARISH-RUG")
    assert "b2" in [b.reference for b in product.batches]


async def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    await handlers.add_batch(
        uow=uow, reference="batch1", sku="COMPLICATED-LAMP",
        purchased_quantity=100, eta=None, allocations=set()
    )
    result = await handlers.allocate(uow=uow, orderid="o1", sku="COMPLICATED-LAMP", qty=10)
    assert result == "batch1"


async def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    await handlers.add_batch(
        uow=uow, reference="b1", sku="AREALSKU",
        purchased_quantity=100, eta=None, allocations=set()
    )
    try:
        await handlers.allocate(uow=uow, orderid="o1", sku="NONEXISTENTSKU", qty=10)
    except handlers.InvalidSku as e:
        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e


async def test_sends_email_on_out_of_stock_error():
    uow = FakeUnitOfWork()
    await handlers.add_batch(
        uow=uow, reference="b1", sku="POPULAR-CURTAINS",
        purchased_quantity=9, eta=None, allocations=set()
    )

    with mock.patch("allocation.adapters.email.send_mail") as mock_send_mail:
        await handlers.allocate("o1", "POPULAR-CURTAINS", 10, uow)
        assert mock_send_mail.call_args == mock.call(
            "stock@made.com",
            "Out of stock for POPULAR-CURTAINS",
        )
