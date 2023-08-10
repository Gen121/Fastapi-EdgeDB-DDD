from dataclasses import dataclass


@dataclass
class Event:
    pass


@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str


@dataclass
class OutOfStock(Event):
    sku: str
