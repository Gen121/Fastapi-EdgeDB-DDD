import datetime
import traceback

import pytest

from allocation.adapters import pyd_model as model
from allocation.services import unit_of_work

from .utils import insert_batch


async def get_allocated_batch_ref(async_client_db, orderid, sku):
    [orderlineid] = await async_client_db.query(
        "SELECT OrderLine { id } FILTER .orderid=<str>$orderid AND .sku=<str>$sku",
        orderid=orderid, sku=sku,
    )
    orderlineid = orderlineid.id
    [batchref] = await async_client_db.query(
        "SELECT Batch { reference } FILTER .allocations.id=<uuid>$orderlineid",
        orderlineid=orderlineid,
    )
    batchref = batchref.reference
    return batchref


async def test_uow_can_retrieve_a_batch_and_allocate_to_it(async_client_db, random_batchref, random_sku, random_orderid):
    batchref_expected, sku, order_id = random_batchref, f"HIPSTER-WORKBENCH-{random_sku}", random_orderid
    await insert_batch(async_client_db, batchref_expected, sku, 100, datetime.date(2011, 1, 2))

    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    async with uow:
        product = await uow.products.get(sku=sku)
        line = model.OrderLine(orderid=order_id, sku=sku, qty=10)
        if not product:
            assert False
        product.allocate(line)
        await uow.products.add(product)
        await uow.commit()

    batchref = await get_allocated_batch_ref(async_client_db, order_id, sku)
    assert batchref == batchref_expected


async def test_rolls_back_uncommitted_work_by_default(async_client_db, random_sku):
    sku_expected = f"rolls_back_uncommitted_work_by_default_{random_sku}"
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    product = model.Product(sku=sku_expected, version_number=1, batches=[])
    async with uow:
        await uow.products.add(product)

    rows = list(await async_client_db.query(f'SELECT Product {{ * }} FILTER .sku = "{sku_expected}"'))
    assert rows == []


async def test_rolls_back_on_error(async_client_db, random_sku):
    class MyException(Exception):
        pass

    sku_expected = f"rolls_back_on_error_{random_sku}"
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    product = model.Product(sku=sku_expected, version_number=1, batches=[])
    try:
        async with uow:
            await uow.products.add(product)
            raise MyException()
    except MyException as e:
        with pytest.raises(MyException):
            raise e

    rows = list(await async_client_db.query(f'SELECT Product {{ * }} FILTER .sku = "{sku_expected}"'))
    assert rows == []
