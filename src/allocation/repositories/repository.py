from __future__ import annotations

import abc

import edgedb

import allocation.adapters.pyd_model as model


class SynchronousUpdateError(Exception):
    pass


class AbstractRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: set[model.Product] = set()

    async def add(self, product: model.Product) -> None:
        await self._add(product)
        self.seen.add(product)

    async def get(self, sku: str) -> model.Product | None:
        product = await self._get(sku=sku)
        if product:
            self.seen.add(product)
        return product

    async def get_by_batchref(self, batchref: str) -> model.Product | None:
        product = await self._get_by_batchref(batchref=batchref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    async def _add(self, product: model.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get(self, *args, **kwargs) -> model.Product | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_by_batchref(self, *args, **kwargs) -> model.Product | None:
        raise NotImplementedError

    async def list(self) -> list[model.Batch] | None:
        raise NotImplementedError


class EdgeDBRepository(AbstractRepository):
    def __init__(self, async_client_db) -> None:
        super().__init__()
        self.client: edgedb.AsyncIOClient = async_client_db

    async def _get(
        self, sku: str | None = None, batchref: str | None = None, allocations: bool = True
    ) -> model.Product | None:
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
                FILTER .sku ?= <optional str>$sku
                OR .batches.reference ?= <optional str>$reference
                LIMIT 1

            """,
            sku=sku,
            reference=batchref,
        )
        return model.Product.model_validate(obj_) if obj_ else None

    async def _get_by_batchref(self, batchref: str | None) -> model.Product | None:
        return await self._get(batchref=batchref)

    async def _add(self, product: model.Product) -> None:
        product_db = await self.client.query_single(
            """SELECT Product { version_number } FILTER .sku=<str>$sku""", sku=product.sku
        )
        if product_db and product_db.version_number >= product.version_number:
            raise SynchronousUpdateError()
        await self.add_product(product)
        self.seen.add(product)
        if hasattr(product, "batches"):
            if product.batches is not None:
                for batch in product.batches:
                    await self.add_batch(batch)

    async def add_product(self, product: model.Product):
        data = product.model_dump_json(exclude={"batches"})
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
            data=data,
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
                INSERT OrderLine {
                    orderid := <str>order_line['orderid'],
                    qty := <int16>order_line['qty'],
                    sku := <str>order_line['sku'],
                    allocated_in := new_batch
                }
            );
            WITH obj := <json>$data,
            SELECT Batch FILTER .reference = <str>obj['reference'];
            """,
            data=data,
        )

    async def list(self) -> list[model.Batch]:
        objects = await self.client.query("""SELECT Batch {**}""")
        return [model.Batch.model_validate(obj) for obj in objects]
