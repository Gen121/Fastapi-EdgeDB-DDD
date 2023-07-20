import datetime

import pytest

from allocation.adapters import pyd_model as model
from allocation.services import unit_of_work


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


async def test_uow_can_retrieve_a_batch_and_allocate_to_it(async_client_db, random_batchref):
    batchref_expected = random_batchref
    await insert_batch(async_client_db, batchref_expected, "HIPSTER-WORKBENCH", 100, datetime.date(2011, 1, 2))

    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    async with uow:
        batch = await uow.batches.get(reference=batchref_expected)
        line = model.OrderLine(orderid="o1", sku="HIPSTER-WORKBENCH", qty=10)
        batch.allocate(line)
        await uow.batches.add(batch)
        await uow.commit()

    batchref = await get_allocated_batch_ref(async_client_db, "o1", "HIPSTER-WORKBENCH")
    assert batchref == batchref_expected


async def test_rolls_back_uncommitted_work_by_default(async_client_db, random_batchref):
    batchref_expected = (f"rolls_back_uncommitted_work_by_default_{random_batchref}")
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    batch = model.Batch(
        reference=batchref_expected,
        sku="MEDIUM-PLINTH",
        purchased_quantity=100,
        eta=datetime.date(2011, 1, 2)
    )
    async with uow:
        await uow.batches.add(batch)

    rows = list(await async_client_db.query(f'SELECT Batch {{*}} filter .reference = "{batchref_expected}"'))
    assert rows == []


async def test_rolls_back_on_error(async_client_db, random_batchref):
    class MyException(Exception):
        pass

    batchref_expected = f"rolls_back_on_error_{random_batchref}"
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    batch = model.Batch(
        reference=batchref_expected,
        sku="MEDIUM-PLINTH",
        purchased_quantity=100,
        eta=datetime.date(2011, 1, 2)
    )
    try:
        async with uow:
            await uow.batches.add(batch)
            raise MyException()
    except MyException as e:
        with pytest.raises(MyException):
            raise e

    rows = list(await async_client_db.query(f'SELECT Batch {{*}} filter .reference = "{batchref_expected}"'))
    assert rows == []
