from datetime import date
import uuid

import allocation.domain.model as model
from allocation.adapters.pyd_model import Batch, OrderLine
from allocation.services import unit_of_work


class InvalidSku(Exception):
    pass


class OutOfStockInBatch(Exception):
    pass


async def is_valid_sku(sku, batches) -> bool:
    return sku in {b.sku for b in batches}


async def allocate_in_current_batch(
    batch: Batch,
    orrderlines: set[dict]
) -> None:
    to_allocate = [OrderLine(**orderline) for orderline in orrderlines]
    for orderline in to_allocate:
        batch.allocate(orderline)
    if len(batch.allocations) < len(to_allocate):
        raise OutOfStockInBatch(
            "There is not enough stock for the {line.sku} article in this batch")


async def get_batch(
    uow: unit_of_work.EdgedbUnitOfWork,
    reference: str | None = None,
    uuid: uuid.UUID | None = None,
) -> Batch:
    async with uow:
        res = await uow.batches.get(reference=reference, uuid=uuid)
        await uow.commit()
    return res


async def get_all(
        uow: unit_of_work.EdgedbUnitOfWork,
) -> list[Batch]:
    async with uow:
        res = await uow.batches.list()
        await uow.commit()
    return res


async def add_batch(
    uow: unit_of_work.EdgedbUnitOfWork,
    reference: str, sku: str, purchased_quantity: int, eta: date | None,
    allocations: set[dict] | None,
) -> None:
    batch = Batch(
        reference=reference, sku=sku, purchased_quantity=purchased_quantity, eta=eta
    )
    if allocations:
        await allocate_in_current_batch(batch, allocations)
    async with uow:
        await uow.batches.add(batch)
        await uow.commit()


async def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.EdgedbUnitOfWork,
) -> str:
    line = OrderLine(orderid=orderid, sku=sku, qty=qty)
    async with uow:
        batches = await uow.batches.list()
        if not await is_valid_sku(line.sku, batches):
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = model.allocate(line, batches)
        [current_batch] = [b for b in batches if b.reference == batchref]
        await uow.batches.add(current_batch)
        await uow.commit()
    return batchref
