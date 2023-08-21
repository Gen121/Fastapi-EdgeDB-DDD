from allocation.services import unit_of_work


async def allocations(
    orderid: str, uow: unit_of_work.EdgedbUnitOfWork
) -> list[dict[str, str]]:
    async with uow:
        results = await uow.async_client.query(
            """ SELECT AllocationsView {sku, batchref}
                  FILTER .orderid = <str>$orderid
            """,
            orderid=orderid,
        )
    return [{"sku": result.sku, "batchref": result.batchref} for result in results]
