from pyd_model import OrderLine
from repository import AbstractRepository
import model


class InvalidSku(Exception):
    pass


async def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


async def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = await repo.list()
    if not await is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batchref = model.allocate(line, batches)
    [current_batch] = [b for b in batches if b.reference == batchref]
    await repo.add(current_batch)
    return batchref
