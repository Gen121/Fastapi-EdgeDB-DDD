from allocation.services import unit_of_work


async def allocations(orderid: str, uow: unit_of_work.EdgedbUnitOfWork) -> list[dict[str, str]]:
    async with uow:
        results = await uow.async_client.query(
            """SELECT Batch {sku, reference}
                FILTER .allocations .orderid = <str>$orderid
            """,
            orderid=orderid
        )
    return [{"sku": result.sku, "batchref": result.reference} for result in results]
