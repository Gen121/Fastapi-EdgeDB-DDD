from unittest import mock

import pytest

import allocation.domain.model as model
import allocation.repositories.repository as repository
import allocation.services.product_services as product_services
from allocation.services.unit_of_work import email_sender


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        self._products = set(products)
        self.seen = set()

    async def add(self, product):
        self.seen.add(product)
        self._products.add(product)

    async def get(self, sku) -> model.Product | None:
        product = next((p for p in self._products if p.sku == sku), None)
        if product:
            self.seen.add(product)
        return product


@email_sender
class FakeUnitOfWork():
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
    await product_services.add_batch(uow, "b1", "CRUNCHY-ARMCHAIR", 100, None, set())
    assert await uow.products.get(sku="CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


async def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    await product_services.add_batch(uow, "b1", "GARISH-RUG", 100, None, set())
    await product_services.add_batch(uow, "b2", "GARISH-RUG", 99, None, set())
    product = await uow.products.get("GARISH-RUG")
    assert "b2" in [b.reference for b in product.batches]


async def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    await product_services.add_batch(
        uow=uow, reference="batch1", sku="COMPLICATED-LAMP",
        purchased_quantity=100, eta=None, allocations=set()
    )
    result = await product_services.allocate(uow=uow, orderid="o1", sku="COMPLICATED-LAMP", qty=10)
    assert result == "batch1"


async def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    await product_services.add_batch(
        uow=uow, reference="b1", sku="AREALSKU",
        purchased_quantity=100, eta=None, allocations=set()
    )
    try:
        await product_services.allocate(uow=uow, orderid="o1", sku="NONEXISTENTSKU", qty=10)
    except product_services.InvalidSku as e:
        with pytest.raises(product_services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e


async def test_sends_email_on_out_of_stock_error():
    uow = FakeUnitOfWork()
    await product_services.add_batch(
        uow=uow, reference="b1", sku="POPULAR-CURTAINS",
        purchased_quantity=9, eta=None, allocations=set()
    )

    with mock.patch("allocation.adapters.email.send_mail") as mock_send_mail:
        await product_services.allocate("o1", "POPULAR-CURTAINS", 10, uow)
        assert mock_send_mail.call_args == mock.call(
            "stock@made.com",
            f"Out of stock for POPULAR-CURTAINS",
        )
