import abc

import edgedb

import allocation.adapters.pyd_model as model


class SynchronousUpdateError(Exception):
    pass


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, batch: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, sku) -> model.Product | None:
        raise NotImplementedError

    async def list(self) -> list[model.Batch]:
        raise NotImplementedError


class EdgeDBRepository(AbstractRepository):
    def __init__(self, async_client_db) -> None:
        self.client: edgedb.AsyncIOClient = async_client_db

    async def get(self, sku: str, allocations: bool = True):
        """Return Product by SKU."""
        obj_ = await self.client.query_single(
            f""" SELECT Product {{
                  sku, version_number,
                  batches: {{
                      reference,
                      sku,
                      eta,
                      purchased_quantity,
                      {"allocations: { orderid, sku, qty }" if allocations else ""}
                  }}
                }}
                FILTER .sku = <str>$sku
                LIMIT 1
            """,
            sku=sku)
        return model.Product.model_validate(obj_) if obj_ else None

    async def add(self, product: model.Product):
        product_db = await self.client.query_single(
            """SELECT Product { version_number } FILTER .sku=<str>$sku""",
            sku=product.sku
        )
        if product_db and product_db.version_number >= product.version_number:
            raise SynchronousUpdateError()
        return await self._add(product)

    async def _add(self, product: model.Product) -> None:
        await self.add_product(product)
        for batch in product.batches:
            await self.add_batch(batch)

    async def add_product(self, product: model.Product):
        data = product.model_dump_json(exclude={'batches'})
        await self.client.query(
            """WITH
            obj := <json>$data,
            INSERT Product {
                sku := <str>obj['sku'],
                version_number := <int16>obj['version_number'],
            }
            UNLESS CONFLICT ON .sku ELSE (
                UPDATE Product SET {
                sku := <str>obj['sku'],
                version_number := <int16>obj['version_number'],
                }
            )
            """,
            data=data
        )

    async def add_batch(self, batch: model.Batch) -> None:
        data = batch.model_dump_json()
        await self.client.query(
            """WITH
            obj := <json>$data,
            list_orders := <array<json>>obj['allocations'] ?? [<json>{}],
            new_batch := (INSERT Batch {
                reference := <str>obj['reference'],
                sku := <str>obj['sku'],
                eta := <cal::local_date>obj['eta'],
                purchased_quantity := <int16>obj['purchased_quantity'],
            }
            UNLESS CONFLICT ON .reference ELSE (
                UPDATE Batch SET {
                reference := <str>obj['reference'],
                sku := <str>obj['sku'],
                eta := <cal::local_date>obj['eta'],
                purchased_quantity := <int16>obj['purchased_quantity'],
                }
            )),
            for order_line in array_unpack(list_orders) union (
                SELECT (
                INSERT OrderLine {
                    orderid := <str>order_line['orderid'],
                    qty := <int16>order_line['qty'],
                    sku := <str>order_line['sku'],
                    allocated_in := new_batch
                } UNLESS CONFLICT ON .orderid ELSE (
                    UPDATE OrderLine
                    SET {
                        orderid := <str>order_line['orderid'],
                        qty := <int16>order_line['qty'],
                        sku := <str>order_line['sku'],
                        allocated_in := new_batch
                    }
                )
                )
            );
            WITH obj := <json>$data,
            SELECT Batch FILTER .reference = <str>obj['reference'];
            """,
            data=data
        )

    async def list(self) -> list[model.Batch]:
        objects = await self.client.query(
            """SELECT Batch {**}"""
        )
        return [model.Batch.model_validate(obj) for obj in objects]
