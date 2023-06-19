import abc
from uuid import UUID
import edgedb
import pyd_model
import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: pyd_model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> pyd_model.Batch:
        raise NotImplementedError


class EdgeDBRepository(AbstractRepository):
    def __init__(self, client):
        self.client: edgedb.Client = client

    def get(self, key: UUID | str) -> pyd_model.Batch:
        if isinstance(key, UUID):
            return self.get_batch_by_id(key)
        return self.get_batch_by_reference(key)

    def add(self, batch: model.Batch) -> None:
        return self.add_batch(batch)

    def add_batch(self, batch: model.Batch) -> None:
        self.client.query(
            """
            INSERT Batch {
                purchased_quantity := <int16>$purchased_quantity,
                eta := <cal::local_date>$eta,
                reference := <str>$reference,
                sku := <str>$sku,
            }
            """,
            purchased_quantity=batch._purchased_quantity,
            eta=batch.eta,
            reference=batch.reference,
            sku=batch.sku,
        )

    def get_batch_by_reference(self, reference: str) -> pyd_model.Batch:
        batch = self.client.query_required_single_json(
            "SELECT Batch {**} FILTER .reference = <str>$reference LIMIT 1",
            reference=reference,
        )
        return pyd_model.Batch.parse_raw(batch)

    def get_batch_by_id(self, id: UUID) -> pyd_model.Batch:
        batch = self.client.query_required_single_json(
            "SELECT Batch {**} FILTER .id = <uuid>$id LIMIT 1",
            id=id,
        )
        return pyd_model.Batch.parse_raw(batch)


class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
