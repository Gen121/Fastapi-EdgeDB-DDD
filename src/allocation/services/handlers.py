from dataclasses import asdict
from typing import Sized

from allocation.adapters import redis_eventpublisher, email
from allocation.adapters.pyd_model import Batch, OrderLine, Product
from allocation.domain import commands, events
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
            raise OutOfStockInBatch(
                "There is not enough stock for the {line.sku} article in this batch"
            )


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
    cmd: commands.CreateBatch,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    async with uow:
        product = await uow.products.get(cmd.sku)
        if not product:
            product = Product(sku=cmd.sku, version_number=0, batches=[])
        product.add_batch(
            Batch(reference=cmd.ref, sku=cmd.sku, purchased_quantity=cmd.qty, eta=cmd.eta)
        )
        await uow.products.add(product)
        await uow.commit()


async def allocate(
    cmd: commands.Allocate,
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    line = OrderLine(orderid=cmd.orderid, sku=cmd.sku, qty=cmd.qty)
    async with uow:
        product = await uow.products.get(line.sku)
        if not product:
            raise InvalidSku(f"Invalid sku {line.sku}")
        product.allocate(line)
        await uow.products.add(product)
        await uow.commit()


async def change_batch_quantity(
    cmd: commands.ChangeBatchQuantity,
    uow: unit_of_work.AbstractUnitOfWork,
):
    async with uow:
        product = await uow.products.get_by_batchref(batchref=cmd.ref)
        product.change_batch_quantity(ref=cmd.ref, qty=cmd.qty)
        await uow.commit()


async def reallocate(
    event: events.Deallocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    async with uow:
        product = await uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(**asdict(event)))
        await uow.commit()


async def send_out_of_stock_notification(
    event: events.OutOfStock,
    uow: unit_of_work.AbstractUnitOfWork,
):
    await email.send(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


async def publish_allocated_event(
    event: events.Allocated,
    uow: unit_of_work.AbstractUnitOfWork,
):
    await redis_eventpublisher.publish("line_allocated", event)


async def add_allocation_to_read_model(
    event: events.Allocated,
    uow: unit_of_work.EdgedbUnitOfWork,
):
    async with uow:
        await uow.async_client.query(
            """ INSERT AllocationsView {
                    batchref := <str>$batchref,
                    orderid := <str>$orderid,
                    sku := <str>$sku
            }""",
            batchref=event.batchref,
            orderid=event.orderid,
            sku=event.sku,
        )
        await uow.commit()


async def remove_allocation_from_read_model(
    event: events.Deallocated,
    uow: unit_of_work.EdgedbUnitOfWork,
):
    async with uow:
        await uow.async_client.query(
            """ DELETE AllocationsView
                FILTER
                    .orderid = <str>$orderid and .sku = <str>$sku
            """,
            orderid=event.orderid,
            sku=event.sku,
        )
        await uow.commit()
