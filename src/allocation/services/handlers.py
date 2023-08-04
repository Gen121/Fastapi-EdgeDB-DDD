from typing import Sized

from allocation.adapters.email import send
from allocation.adapters.pyd_model import Batch, OrderLine, Product
from allocation.domain import events
from allocation.services import unit_of_work


class InvalidSku(Exception):
    pass


class OutOfStockInBatch(Exception):
    pass


async def allocate_in_current_batch(batch: Batch, orrderlines: set[dict]) -> None:
    to_allocate = [OrderLine(**orderline) for orderline in orrderlines]
    for orderline in to_allocate:
        batch.allocate(orderline)
    if isinstance(batch.allocations, Sized):
        if len(batch.allocations) < len(to_allocate):
            raise OutOfStockInBatch("There is not enough stock for the {line.sku} article in this batch")


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
    event: events.BatchCreated,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    async with uow:
        product = await uow.products.get(event.sku)
        if not product:
            product = Product(sku=event.sku, version_number=0, batches=[])
        product.add_batch(Batch(reference=event.ref, sku=event.sku, purchased_quantity=event.qty, eta=event.eta))
        await uow.products.add(product)
        await uow.commit()


async def allocate(
    event: events.AllocationRequired,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str | None:
    line = OrderLine(orderid=event.orderid, sku=event.sku, qty=event.qty)
    async with uow:
        product = await uow.products.get(line.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        await uow.products.add(product)
        await uow.commit()
    return batchref


async def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
):
    await send(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )
