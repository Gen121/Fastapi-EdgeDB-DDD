from datetime import date
from typing import Sequence

import allocation.domain.model as model
from allocation.adapters.pyd_model import Batch, OrderLine, Product
from allocation.services import unit_of_work


class InvalidSku(Exception):
    pass


class OutOfStockInBatch(Exception):
    pass


async def is_valid_sku(sku: str, batches: Sequence[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


async def allocate_in_current_batch(
    batch: Batch,
    orrderlines: set[dict]
) -> None:
    to_allocate = [OrderLine(**orderline) for orderline in orrderlines]
    for orderline in to_allocate:
        batch.allocate(orderline)
    if isinstance(batch.allocations, set):
        if len(batch.allocations) < len(to_allocate):
            raise OutOfStockInBatch(
                "There is not enough stock for the {line.sku} article in this batch")


async def get(
    uow: unit_of_work.EdgedbUnitOfWork,
    sku: str,
) -> Product:
    async with uow:
        res = await uow.products.get(sku=sku)
        await uow.commit()
    return res


async def get_all(
        uow: unit_of_work.EdgedbUnitOfWork,
) -> list[Batch]:
    async with uow:
        res = await uow.products.list()
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
        await uow.products.add(batch)
        await uow.commit()


async def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.EdgedbUnitOfWork,
) -> str:
    line = OrderLine(orderid=orderid, sku=sku, qty=qty)
    async with uow:
        product: model.Product = await uow.products.get(sku)
        if not await is_valid_sku(line.sku, product.batches):
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = product.allocate(line)
        [current_batch] = [b for b in product.batches if b.reference == batchref]
        await uow.products.add(current_batch)
        await uow.commit()
    return batchref
