# pylint: disable=too-few-public-methods
from datetime import date
from dataclasses import dataclass


class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: date | None


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
