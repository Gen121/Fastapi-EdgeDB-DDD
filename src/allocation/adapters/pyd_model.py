from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

import allocation.domain.model as model
from allocation.domain.events import Event  # noqa
from allocation.domain.model import OutOfStock  # noqa


class OrderLine(BaseModel, model.OrderLine):
    sku: str
    qty: int
    orderid: str
    id: UUID | None = Field(default=None, exclude=True)

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True
    )

    def __hash__(self):
        return hash((self.sku, self.qty, self.orderid))

    def __eq__(self, other):
        if not isinstance(other, model.OrderLine):
            return False

        return all((
            other.orderid == self.orderid,
            other.sku == self.sku,
            other.qty == self.qty,
        ))


class OrderLineWithAllocatedIn(OrderLine):
    allocated_in: Batch


class Batch(BaseModel, model.Batch):
    id: UUID | None = Field(default=None, exclude=True,)
    reference: str
    sku: str
    eta: date | None
    purchased_quantity: int
    allocations: set[OrderLine] | None = Field(default_factory=set)

    model_config = ConfigDict(
        from_attributes=True
    )

    def __hash__(self):
        return hash(self.reference)

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference


class Product(BaseModel, model.Product):
    id: UUID | None = Field(default=None, exclude=True,)
    sku: str
    batches: list[Batch] | None = Field(default_factory=list)
    version_number: int
    events: list = Field(default_factory=list, exclude=True,)

    model_config = ConfigDict(
        from_attributes=True,
    )

    def __hash__(self):
        return hash(self.sku)


OrderLineWithAllocatedIn.model_rebuild()
