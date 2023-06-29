# pylint: disable=protected-access
import datetime
import random
import zoneinfo
from uuid import UUID
import json

import repository
from pyd_model import Batch, OrderLine


def random_num() -> int:
    return random.randint(10000, 99999)


def test_repository_can_save_a_batch(client):
    bath_ref = f'can_save_a_batch_{random_num()}'
    tz = zoneinfo.ZoneInfo("America/Buenos_Aires")
    date = datetime.datetime.now(tz).date()
    batch = Batch(
        reference=bath_ref, sku="RUSTY-SOAPDISH",
        purchased_quantity=100, eta=date,
    )
    repo = repository.EdgeDBRepository(client)
    repo.add(batch)
    json_ = client.query_required_single_json(
        """SELECT Batch {*}
            FILTER .reference = <str>$reference and .sku = <str>$sku
            LIMIT 1;
        """,
        reference=bath_ref,
        sku="RUSTY-SOAPDISH",
    )
    batch_db = Batch.parse_raw(json_)
    assert batch_db == batch


def insert_order_line(client, orderid) -> UUID:
    client.query(
        """INSERT OrderLine {
            orderid := <str>$orderid,
            sku := <str>$sku,
            qty := <int16>$qty
        }""",
        orderid=orderid,
        sku="GENERIC-SOFA",
        qty=12,
    )
    order_id = client.query(
        """SELECT OrderLine {id}
            FILTER .orderid = <str>$orderid and .sku=<str>$sku
        """,
        orderid=orderid,
        sku="GENERIC-SOFA",
    )[0].id
    return order_id


def insert_batch(client, reference: str) -> UUID:
    client.query(
        """INSERT Batch {
            reference := <str>$reference,
            sku := <str>$sku,
            purchased_quantity := <int16>$purchased_quantity,
        }""",
        reference=reference,
        sku="GENERIC-SOFA",
        purchased_quantity=100,
    )
    batch_id = client.query(
        """SELECT Batch {id}
            FILTER .reference = <str>$reference and .sku=<str>$sku""",
        reference=reference,
        sku="GENERIC-SOFA"
    )[0].id
    return batch_id


def add_allocateion_to_batch_by_ids(client, orderline_id: UUID, batch_id: UUID) -> None:
    client.query(
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


def test_repository_can_retrieve_a_batch_with_allocations(client):
    orderid = f'inserted_order_line_{random_num()}'
    orderline_id = insert_order_line(client, orderid)
    batch1_id = insert_batch(
        client, f"repository_can_retrieve_a_batch_with_{orderid}")
    insert_batch(client, f"inserted_batch_{random_num()}")
    add_allocateion_to_batch_by_ids(client, orderline_id, batch1_id)

    repo = repository.EdgeDBRepository(client)
    retrieved: Batch = repo.get(
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


def get_allocations(client, reference):
    json_: str = client.query_json(
        """
        SELECT OrderLine {orderid}
            FILTER .allocated_in .reference = <str>$reference
        """,
        reference=reference,
    )
    return {i['orderid'] for i in json.loads(json_)}


def test_updating_a_batch(client):
    order1 = OrderLine(orderid=f"order_{random_num()}", sku="WEATHERED-BENCH", qty=10)
    order2 = OrderLine(orderid=f"order_{random_num()}", sku="WEATHERED-BENCH", qty=20)
    batch_reference = f"batch_{random_num()}"
    batch = Batch(reference=batch_reference, sku="WEATHERED-BENCH",
                  purchased_quantity=100, eta=None)
    batch.allocate(order1)

    repo = repository.EdgeDBRepository(client)
    repo.add(batch)

    batch.allocate(order2)
    repo.add(batch)

    assert get_allocations(client, batch_reference) == {order1.orderid, order2.orderid}
