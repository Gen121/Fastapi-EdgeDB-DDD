import datetime
import uuid

from allocation.domain import model
from allocation.services import unit_of_work


def random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def random_batchref(name: str | int = "") -> str:
    return f"batch-{name}-{random_suffix()}"


async def insert_batch(async_client_db, ref, sku, qty, eta):
    await async_client_db.query(
        """insert Batch {
            reference := <str>$reference,
            sku := <str>$sku,
            eta := <cal::local_date>$eta,
            purchased_quantity := <int16>$purchased_quantity
        }""",
        reference=ref, sku=sku, purchased_quantity=qty, eta=eta
    )


async def get_allocated_batch_ref(async_client_db, orderid, sku):
    [orderlineid] = await async_client_db.query(
        "SELECT OrderLine {id} FILTER .orderid=<str>$orderid AND .sku=<str>$sku",
        orderid=orderid, sku=sku,
    )
    orderlineid = orderlineid.id
    [batchref] = await async_client_db.query(
        "SELECT Batch {reference} FILTER .allocations.id=<uuid>$orderlineid",
        orderlineid=orderlineid,
    )
    batchref = batchref.reference
    return batchref


async def test_uow_can_retrieve_a_batch_and_allocate_to_it(async_client_db):
    batchref_expected = random_batchref("uow")
    await insert_batch(async_client_db, batchref_expected, "HIPSTER-WORKBENCH", 100, datetime.date(2011, 1, 2))

    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    async with uow:
        batch = await uow.batches.get(reference=batchref_expected)
        line = model.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        batch.allocate(line)
        await uow.batches.add(batch)

    batchref = await get_allocated_batch_ref(async_client_db, "o1", "HIPSTER-WORKBENCH")
    assert batchref == batchref_expected
