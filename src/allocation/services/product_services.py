from datetime import date
from typing import Sized

from allocation.adapters.pyd_model import Batch, OrderLine, Product
from allocation.services import unit_of_work


class InvalidSku(Exception):
    pass


class OutOfStockInBatch(Exception):
    pass


async def allocate_in_current_batch(
    batch: Batch,
    orrderlines: set[dict]
) -> None:
    to_allocate = [OrderLine(**orderline) for orderline in orrderlines]
    for orderline in to_allocate:
        batch.allocate(orderline)
    if isinstance(batch.allocations, Sized):
        if len(batch.allocations) < len(to_allocate):
            raise OutOfStockInBatch(
                "There is not enough stock for the {line.sku} article in this batch")


async def get(
    uow: unit_of_work.AbstractUnitOfWork,
    sku: str,
) -> Product | None:
    async with uow:
        res = await uow.products.get(sku=sku)
        await uow.commit()
    return res


async def get_all(
        uow: unit_of_work.AbstractUnitOfWork,
) -> list[Batch] | None:
    async with uow:
        res = await uow.products.list()
        await uow.commit()
    return res


async def add_batch(
    uow: unit_of_work.AbstractUnitOfWork,
    reference: str, sku: str, purchased_quantity: int, eta: date | None,
    allocations: set[dict] | None,
) -> None:
    batch = Batch(
        reference=reference, sku=sku, purchased_quantity=purchased_quantity, eta=eta
    )
    if allocations:
        await allocate_in_current_batch(batch, allocations)
    async with uow:
        product = await uow.products.get(sku)
        if not product:
            product = Product(sku=sku, version_number=0, batches=[])
        product.add_batch(batch)
        await uow.products.add(product)
        await uow.commit()


async def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str | None:
    line = OrderLine(orderid=orderid, sku=sku, qty=qty)
    async with uow:
        product = await uow.products.get(sku)
        if not product:
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = product.allocate(line)
        await uow.products.add(product)
        await uow.commit()
    return batchref
