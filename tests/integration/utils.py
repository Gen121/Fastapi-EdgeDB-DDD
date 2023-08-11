import datetime
import json
from uuid import UUID

import edgedb


async def insert_product(  # TODO
    async_client_db: edgedb.AsyncIOClient, sku: str, version_number: int
) -> UUID | None:
    try:
        product = await async_client_db.query(
            "INSERT Product {sku := <str>$sku, version_number := <int16>$version_number}",
            sku=sku,
            version_number=version_number,
        )
        return product[0].id
    except edgedb.errors.ConstraintViolationError:
        pass
    return None


async def insert_batch(
    async_client_db: edgedb.AsyncIOClient,
    ref,
    sku,
    qty=100,
    eta=datetime.date(2011, 1, 2),
    version_number=1,
) -> UUID:
    await insert_product(async_client_db, sku, version_number)
    batch = await async_client_db.query(
        """INSERT Batch {
            reference := <str>$reference,
            sku := <str>$sku,
            eta := <cal::local_date>$eta,
            purchased_quantity := <int16>$purchased_quantity
        }""",
        reference=ref,
        sku=sku,
        purchased_quantity=qty,
        eta=eta,
    )
    return batch[0].id


async def insert_order_line(
    async_client_db: edgedb.AsyncIOClient,
    orderid,
    sku,
    qty=10,
) -> UUID:
    orderline = await async_client_db.query(
        """INSERT OrderLine {
            orderid := <str>$orderid,
            sku := <str>$sku,
            qty := <int16>$qty
        }""",
        orderid=orderid,
        sku=sku,
        qty=qty,
    )
    return orderline[0].id


async def add_allocateion_to_batch_by_ids(
    async_client_db: edgedb.AsyncIOClient,
    orderline_id: UUID,
    batch_id: UUID,
) -> None:
    await async_client_db.query(
        """UPDATE OrderLine
            FILTER .id = <uuid>$orderline_id
            SET { allocated_in := (
                    SELECT Batch FILTER .id = <uuid>$batch_id
            )
        }""",
        orderline_id=orderline_id,
        batch_id=batch_id,
    )


async def get_allocations(async_client_db: edgedb.AsyncIOClient, reference: str) -> set[UUID]:
    json_ = await async_client_db.query_json(
        """
        SELECT OrderLine {orderid}
            FILTER .allocated_in .reference = <str>$reference
        """,
        reference=reference,
    )
    return {i["orderid"] for i in json.loads(json_)}


async def get_allocated_batch_ref(async_client_db, orderid, sku):
    [orderlineid] = await async_client_db.query(
        "SELECT OrderLine { id } FILTER .orderid=<str>$orderid AND .sku=<str>$sku",
        orderid=orderid,
        sku=sku,
    )
    orderlineid = orderlineid.id
    [batchref] = await async_client_db.query(
        "SELECT Batch { reference } FILTER .allocations.id=<uuid>$orderlineid",
        orderlineid=orderlineid,
    )
    batchref = batchref.reference
    return batchref
