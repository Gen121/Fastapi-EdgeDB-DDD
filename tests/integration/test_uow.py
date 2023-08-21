import datetime

import pytest

from allocation.adapters import pyd_model as model
from allocation.services import unit_of_work

from .utils import get_allocated_batch_ref, insert_batch


async def test_uow_can_retrieve_a_batch_and_allocate_to_it(
    async_client_db, random_batchref, random_sku, random_orderid
):
    batchref_expected, sku, order_id = (
        random_batchref(),
        f"HIPSTER-WORKBENCH-{random_sku()}",
        random_orderid(),
    )
    await insert_batch(
        async_client_db, batchref_expected, sku, 100, datetime.date(2011, 1, 2)
    )

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
    sku_expected = f"rolls_back_uncommitted_work_by_default_{random_sku()}"
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    product = model.Product(sku=sku_expected, version_number=1, batches=[])
    async with uow:
        await uow.products.add(product)

    rows = list(
        await async_client_db.query(
            f""" SELECT Product {{ * }} FILTER .sku = "{sku_expected}" """
        )
    )
    assert rows == []


async def test_rolls_back_on_error(async_client_db, random_sku):
    class MyException(Exception):
        pass

    sku_expected = f"rolls_back_on_error_{random_sku()}"
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    product = model.Product(sku=sku_expected, version_number=1, batches=[])
    try:
        async with uow:
            await uow.products.add(product)
            raise MyException()
    except MyException as e:
        with pytest.raises(MyException):
            raise e

    rows = list(
        await async_client_db.query(
            f""" SELECT Product {{ * }} FILTER .sku = "{sku_expected}" """
        )
    )
    assert rows == []


# TODO: implement testing of Optimistic parallelism with version numbers

# async def try_to_allocate(orderid, sku, exceptions, async_client_db):
#     line = model.OrderLine(orderid=orderid, sku=sku, qty=10)
#     uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
#     try:
#         async with uow:
#             product = await uow.products.get(sku=sku)
#             if isinstance(product, model.Product):
#                 product.allocate(line)
#                 await uow.products.add(product)
#             # await asyncio.sleep(0.2)  # Use asyncio.sleep instead of time.sleep
#             await uow.commit()
#     except Exception as e:
#         print(traceback.format_exc())
#         exceptions.append(e)


# async def test_concurrent_updates_to_version_are_not_allowed(
#     random_sku, random_batchref, async_client_db, random_orderid
# ) -> None:
#     sku, batch = f"concurrent_updates_{random_sku()}", f"concurrent_updates_{random_batchref()}"
#     await insert_batch(async_client_db, batch, sku, 100, datetime.date(2011, 1, 2), 1)
#     order1, order2 = random_orderid(), random_orderid("_2")
#     exceptions: list[Exception] = []

#     await asyncio.gather(
#         try_to_allocate(order1, sku, exceptions, async_client_db),
#         try_to_allocate(order2, sku, exceptions, async_client_db),
#     )

#     [product] = await async_client_db.query(
#         "SELECT Product { version_number } FILTER .sku = <str>$sku",
#         sku=sku,
#     )

#     assert product.version_number == 2

#     [exception] = exceptions
#     assert "не получилось сериализовать доступ из-за параллельного обновления" in str(
#         exception)

#     orders = list(await async_client_db.query(
#         """SELECT Batch { allocations } FILTER .sku = <str>$sku""",
#         sku=sku,
#     ))
#     assert len(orders) == 1

#     uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
#     with uow:
#         await uow.async_client.execute("SELECT 1")
