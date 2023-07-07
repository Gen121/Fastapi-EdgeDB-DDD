from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, validator

import domain.model as model
from domain.model import OutOfStock  # noqa


class OrderLine(BaseModel, model.OrderLine):
    id: UUID | None = Field(default=None)
    sku: str
    qty: int
    orderid: str

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

    class Config:
        orm_mode = True
        frozen = True


class OrderLineWithAllocatedIn(OrderLine):
    allocated_in: Batch


class Batch(BaseModel, model.Batch):
    id: UUID | None = Field(default=None)
    reference: str
    sku: str
    eta: date | None
    purchased_quantity: int
    allocations: set[OrderLine | None] = Field(default_factory=set)

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    class Config:
        orm_mode = True
        json_encoders = {
            set: list
        }

    @validator('allocations', pre=True)
    def convert_to_set(cls, value):
        if isinstance(value, list):
            return set((OrderLine.from_orm(obj) for obj in value))
        return value


OrderLineWithAllocatedIn.update_forward_refs()
