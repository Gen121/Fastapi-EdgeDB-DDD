import abc
import datetime
import model
import functools

import edgedb
from fastapi import FastAPI


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        # self.session.execute('INSERT INTO ??
        ...

    def get(self, reference) -> model.Batch:
        # self.session.execute('SELECT ??
        ...

class EdgeDBRepository(AbstractRepository):
    def __init__(self, client):
        self.client = client

    def add_batch(self, batch: model.Batch):
        self.client.query("""
            INSERT Batch {
                purchased_quantity := <int16>$purchased_quantity,
                eta := <cal::local_date>$eta,
                reference := <str>$reference,
                sku := <str>$sku,
            }
        # """,
        purchased_quantity=batch._purchased_quantity,
        eta=batch.eta,
        reference=batch.reference,
        sku=batch.sku
        )

    def get_batch_by_reference(self, reference) -> model.Batch:
        batch = self.client.query(
            "SELECT Batch {*} FILTER .reference = <str>$reference",
            reference=reference,
            )
        return model.Batch(
            ref=batch.ref,
            sku=batch.sku,
            qty=batch.qty,
            eta=batch.eta,
        )