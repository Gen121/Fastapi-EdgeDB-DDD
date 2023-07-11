import abc
from uuid import UUID

import edgedb

import allocation.adapters.pyd_model as model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, reference) -> model.Batch:
        raise NotImplementedError

    async def list(self) -> list[model.Batch]:
        raise NotImplementedError


class EdgeDBRepository(AbstractRepository):
    def __init__(self, async_client_db):
        self.client: edgedb.AsyncIOClient = async_client_db

    async def get(self, uuid: UUID | None = None, reference: str | None = None) -> model.Batch:
        """Return Batch by UUID or Reference."""
        if not any((uuid, reference)):
            raise Exception('Необходим UUID или reference')

        obj_ = await self.client.query_required_single(
            """select Batch {**}
                filter .id ?= <optional uuid>$uuid
                or .reference ?= <optional str>$reference
                LIMIT 1
            """,
            uuid=uuid, reference=reference)
        return model.Batch.model_validate(obj_)

    async def add(self, batch: model.Batch) -> None:
        return await self.add_batch(batch)

    async def add_batch(self, batch: model.Batch) -> None:
        await self.client.query(
            """with
            obj := <json>$data,
            list_orders := <array<json>>obj['allocations'] ?? [<json>{}],
            new_batch := (insert Batch {
                reference := <str>obj['reference'],
                sku := <str>obj['sku'],
                eta := <cal::local_date>obj['eta'],
                purchased_quantity := <int16>obj['purchased_quantity'],
            }
            unless conflict on .reference else (
                update Batch set {
                reference := <str>obj['reference'],
                sku := <str>obj['sku'],
                eta := <cal::local_date>obj['eta'],
                purchased_quantity := <int16>obj['purchased_quantity'],
                }
            )),
            for order_line in array_unpack(list_orders) union (
                select (
                insert OrderLine {
                    orderid := <str>order_line['orderid'],
                    qty := <int16>order_line['qty'],
                    sku := <str>order_line['sku'],
                    allocated_in := new_batch
                } unless conflict on .orderid else (
                    update OrderLine
                    set {
                        orderid := <str>order_line['orderid'],
                        qty := <int16>order_line['qty'],
                        sku := <str>order_line['sku'],
                        allocated_in := new_batch
                    }
                )
                )
            );
            with obj := <json>$data,
            select Batch filter .reference = <str>obj['reference'];
            """,
            data=batch.model_dump_json()
        )

    async def list(self) -> list[model.Batch]:
        objects = await self.client.query(
            """SELECT Batch {**}"""
        )
        return [model.Batch.model_validate(obj) for obj in objects]
