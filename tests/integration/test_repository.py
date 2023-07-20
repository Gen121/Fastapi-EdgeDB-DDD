# pylint: disable=protected-access
import datetime
import zoneinfo
from uuid import UUID
import json

import pytest

import allocation.repositories.repository as repository
from allocation.adapters.pyd_model import Batch, OrderLine


async def test_repository_can_save_a_batch(async_client_db, random_batchref):
    bath_ref = f'repository_can_save_{random_batchref}'
    tz = zoneinfo.ZoneInfo("America/Buenos_Aires")
    date = datetime.datetime.now(tz).date()
    batch = Batch(
        reference=bath_ref, sku="RUSTY-SOAPDISH",
        purchased_quantity=100, eta=date,
    )
    repo = repository.EdgeDBRepository(async_client_db)
    await repo.add(batch)
    json_ = await async_client_db.query_required_single_json(
        """SELECT Batch {*}
            FILTER .reference = <str>$reference and .sku = <str>$sku
            LIMIT 1;
        """,
        reference=bath_ref,
        sku="RUSTY-SOAPDISH",
    )
    batch_db = Batch.model_validate_json(json_)
    assert batch_db == batch


async def insert_order_line(async_client_db, orderid) -> UUID:
    await async_client_db.query(
        """INSERT OrderLine {
            orderid := <str>$orderid,
            sku := <str>$sku,
            qty := <int16>$qty
        }""",
        orderid=orderid,
        sku="GENERIC-SOFA",
        qty=12,
    )
    order_id = (await async_client_db.query(
        """SELECT OrderLine {id}
            FILTER .orderid = <str>$orderid and .sku=<str>$sku
        """,
        orderid=orderid,
        sku="GENERIC-SOFA",
    ))[0].id
    return order_id


async def insert_batch(async_client_db, reference: str) -> UUID:
    await async_client_db.query(
        """INSERT Batch {
            reference := <str>$reference,
            sku := <str>$sku,
            purchased_quantity := <int16>$purchased_quantity,
        }""",
        reference=reference,
        sku="GENERIC-SOFA",
        purchased_quantity=100,
    )
    batch_id = (await async_client_db.query(
        """SELECT Batch {id}
            FILTER .reference = <str>$reference and .sku=<str>$sku""",
        reference=reference,
        sku="GENERIC-SOFA"
    ))[0].id
    return batch_id


async def add_allocateion_to_batch_by_ids(async_client_db, orderline_id: UUID, batch_id: UUID) -> None:
    await async_client_db.query(
        """
        UPDATE OrderLine
            FILTER .id = <uuid>$orderline_id
            SET { allocated_in := (
                    SELECT Batch FILTER .id = <uuid>$batch_id
                )
            }
        """,
        orderline_id=orderline_id,
        batch_id=batch_id,
    )


async def test_repository_can_retrieve_a_batch_with_allocations(async_client_db, random_batchref, random_orderid):
    orderid = f'with_allocation_{random_orderid}'
    orderline_id = await insert_order_line(async_client_db, orderid)
    batch1_id = await insert_batch(
        async_client_db, f"repository_can_retrieve_a_batch_with_{orderid}")
    await insert_batch(async_client_db, f"inserted_{random_batchref}")
    await add_allocateion_to_batch_by_ids(async_client_db, orderline_id, batch1_id)

    repo = repository.EdgeDBRepository(async_client_db)
    retrieved: Batch = await repo.get(
        reference=f"repository_can_retrieve_a_batch_with_{orderid}")

    expected = Batch(
        reference=f"repository_can_retrieve_a_batch_with_{orderid}",
        sku="GENERIC-SOFA",
        eta=None,
        purchased_quantity=100,
    )

    assert retrieved == expected  # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved.purchased_quantity == expected.purchased_quantity
    assert retrieved.allocations == {
        OrderLine(orderid=orderid, sku="GENERIC-SOFA", qty=12),
    }


async def get_allocations(async_client_db, reference):
    json_ = await async_client_db.query_json(
        """
        SELECT OrderLine {orderid}
            FILTER .allocated_in .reference = <str>$reference
        """,
        reference=reference,
    )
    return {i['orderid'] for i in json.loads(json_)}


async def test_repository_updating_a_batch(async_client_db, random_orderid, random_batchref):
    order1 = OrderLine(
        orderid=f"updating_a_batch_{random_orderid}", sku="WEATHERED-BENCH", qty=10)
    order2 = OrderLine(
        orderid=f"updating_a_batch_{random_orderid}_2", sku="WEATHERED-BENCH", qty=20)
    batch_reference = f"updating_a_batch_{random_batchref}"
    batch = Batch(reference=batch_reference, sku="WEATHERED-BENCH",
                  purchased_quantity=100, eta=None)
    batch.allocate(order1)

    repo = repository.EdgeDBRepository(async_client_db)
    await repo.add(batch)

    batch.allocate(order2)
    await repo.add(batch)

    assert await get_allocations(async_client_db, batch_reference) == {order1.orderid, order2.orderid}


async def test_repository_error_for_get_without_parametrs(async_client_db):
    repo = repository.EdgeDBRepository(async_client_db)
    try:
        await repo.get()
    except Exception as e:
        with pytest.raises(Exception, match="Необходим UUID или reference"):
            raise e


async def test_repository_get_all_batches(async_client_db, random_batchref):
    batch_reference = f"repository_get_all_{random_batchref}"
    batch_reference_other = f"repository_get_all_{random_batchref}_other"
    batch_id = await insert_batch(async_client_db, batch_reference)
    batch_other_id = await insert_batch(async_client_db, batch_reference_other)
    repo = repository.EdgeDBRepository(async_client_db)
    all_batches = await repo.list()
    all_batches_ids = [b.id for b in all_batches]
    assert batch_id in all_batches_ids
    assert batch_other_id in all_batches_ids
