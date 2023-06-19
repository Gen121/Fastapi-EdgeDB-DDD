from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

import model


class OrderLine(BaseModel, model.OrderLine):
    # primary_key=True, autoincrement=True
    id: UUID | None = Field(default=None, exclude=True)
    sku: str  # String(255)
    qty: int  # Integer, nullable=False
    orderid: str  # String(255)

    def __hash__(self):
        return hash((self.sku, self.qty, self.orderid))


class OrderLineWithAllocatedIn(OrderLine):
    allocted_in: Batch  # noqa


class Batch(BaseModel, model.Batch):

    # primary_key=True, autoincrement=True
    id: UUID | None = Field(default=None, exclude=True)
    reference: str  # String(255)
    sku: str  # String(255)
    purchased_quantity: int  # Integer, nullable=False
    eta: date | None  # Date, nullable=True
    allocations: set[OrderLine] | None = None

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference


OrderLineWithAllocatedIn.update_forward_refs()
