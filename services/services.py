from datetime import date

import domain.model as model
from adapters.pyd_model import Batch, OrderLine
from repositories.repository import AbstractRepository


class InvalidSku(Exception):
    pass


async def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


async def add_batch(
    ref: str, sku: str, qty: int, eta: date | None,
    repo: AbstractRepository, session,
) -> None:
    await repo.add(Batch(reference=ref, sku=sku, purchased_quantity=qty, eta=eta))


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
