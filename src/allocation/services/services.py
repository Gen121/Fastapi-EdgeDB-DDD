from datetime import date

import allocation.domain.model as model
from allocation.adapters.pyd_model import Batch, OrderLine
from allocation.repositories.repository import AbstractRepository


class InvalidSku(Exception):
    pass


class OutOfStockInBatch(Exception):
    pass


async def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


async def allocate_in_current_batch(batch: Batch, orrderlines: set[dict]):
    to_allocate = [OrderLine(**orderline) for orderline in orrderlines]
    for orderline in to_allocate:
        batch.allocate(orderline)
    if len(batch.allocations) < len(to_allocate):
        raise OutOfStockInBatch(
            "There is not enough stock for the {line.sku} article in this batch")


async def add_batch(
    reference: str, sku: str, purchased_quantity: int, eta: date | None,
    allocations: set[dict] | None,
    repo: AbstractRepository, session,
) -> None:
    batch = Batch(
        reference=reference, sku=sku, purchased_quantity=purchased_quantity, eta=eta
    )
    if allocations:
        await allocate_in_current_batch(batch, allocations)
    await repo.add(batch)


async def allocate(
    orderid: str, sku: str, qty: int,
    repo: AbstractRepository, session
) -> str:
    line = OrderLine(orderid=orderid, sku=sku, qty=qty)
    batches = await repo.list()
    if not await is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batchref = model.allocate(line, batches)
    [current_batch] = [b for b in batches if b.reference == batchref]
    await repo.add(current_batch)
    return batchref
