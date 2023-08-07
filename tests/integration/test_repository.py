# pylint: disable=protected-access
import datetime

import allocation.repositories.repository as repository
from allocation.adapters.pyd_model import Batch, OrderLine, Product

from .utils import (add_allocateion_to_batch_by_ids, get_allocations,
                    insert_batch, insert_order_line)


async def test_repository_can_save_a_batch(async_client_db, random_batchref, random_sku):
    repo = repository.EdgeDBRepository(async_client_db)
    bath_ref = f'repository_can_save_{random_batchref()}'
    sku = f'repository_can_save_{random_sku()}'
    batch = Batch(reference=bath_ref, sku=sku,
                  purchased_quantity=100, eta=datetime.date(2011, 1, 2))
    product = Product(sku=sku, batches=[batch], version_number=1)

    await repo.add(product)
    json_ = await async_client_db.query_required_single_json(
        """SELECT Batch {*}
            FILTER .reference = <str>$reference and .sku = <str>$sku
            LIMIT 1;
        """,
        reference=bath_ref,
        sku=sku,
    )
    batch_db = Batch.model_validate_json(json_)
    assert batch_db == batch


async def test_repository_can_retrieve_a_batch_with_allocations(async_client_db, random_batchref, random_orderid, random_sku):
    repo = repository.EdgeDBRepository(async_client_db)
    orderid = f'can_retrieve_a_batch_with_allocation_{random_orderid()}'
    sku = f"can_retrieve_a_batch_with_allocations{random_sku()}"
    bath_ref = f"can_retrieve_a_batch_with_{random_batchref()}"

    orderline_id = await insert_order_line(async_client_db, orderid, sku, 10)
    batch1_id = await insert_batch(async_client_db, bath_ref, sku)
    await insert_batch(async_client_db, f"inserted_{random_batchref()}", sku)
    await add_allocateion_to_batch_by_ids(async_client_db, orderline_id, batch1_id)

    product = await repo.get(sku=sku)  # , allocations=True
    [retrieved] = [batch for batch in product.batches if batch.reference == bath_ref]

    expected = Batch(reference=bath_ref, sku=sku, eta=datetime.date(
        2011, 1, 2), purchased_quantity=100,)

    assert retrieved == expected  # Batch.__eq__ only compares reference
    assert retrieved.allocations == {
        OrderLine(orderid=orderid, sku=sku, qty=10),
    }


async def test_repository_updating_a_batch(async_client_db, random_orderid, random_batchref, random_sku):
    repo = repository.EdgeDBRepository(async_client_db)
    orderid = f"updating_a_batch_{random_orderid()}"
    sku = f"updating_a_batch_{random_sku()}"
    batch_ref = f"updating_a_batch_{random_batchref()}"

    order1 = OrderLine(orderid=orderid, sku=sku, qty=10)
    order2 = OrderLine(orderid=orderid + "_2", sku=sku, qty=20)
    batch = Batch(reference=batch_ref, sku=sku, eta=datetime.date(
        2011, 1, 2), purchased_quantity=100,)

    batch.allocate(order1)
    product = Product(sku=sku, batches=[batch], version_number=0)
    await repo.add(product)

    batch.allocate(order2)
    product.version_number += 1
    await repo.add(product)

    assert await get_allocations(async_client_db, batch_ref) == {order1.orderid, order2.orderid}
