import abc
from uuid import UUID
import edgedb
import pyd_model as model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class EdgeDBRepository(AbstractRepository):
    def __init__(self, client):
        self.client: edgedb.Client = client

    def get(self, uuid: UUID | None = None, reference: str | None = None) -> model.Batch:
        """Return Batch by UUID or Reference."""
        if not any((uuid, reference)):
            raise Exception('Необходим UUID или reference')

        obj_ = self.client.query_required_single(
            """select Batch {**}
                filter .id ?= <optional uuid>$uuid
                or .reference ?= <optional str>$reference
                LIMIT 1
            """,
            uuid=uuid, reference=reference)
        return model.Batch.from_orm(obj_)

    def add(self, batch: model.Batch) -> None:
        return self.add_batch(batch)

    def add_batch(self, batch: model.Batch) -> None:
        batch.allocations = list(batch.allocations)  # noqa
        self.client.query(
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
            data=batch.json()
        )
        batch.allocations = set(batch.allocations)

    def get_batch_by_reference(self, reference: str) -> model.Batch:
        batch = self.client.query_required_single_json(
            "SELECT Batch {**} FILTER .reference = <str>$reference LIMIT 1",
            reference=reference,
        )
        return model.Batch.parse_raw(batch)

    def get_batch_by_id(self, id: UUID) -> model.Batch:
        batch = self.client.query_required_single_json(
            "SELECT Batch {**} FILTER .id = <uuid>$id LIMIT 1",
            id=id,
        )
        return model.Batch.parse_raw(batch)


class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
