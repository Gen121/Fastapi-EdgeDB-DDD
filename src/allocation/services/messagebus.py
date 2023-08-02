from typing import Callable

from allocation.domain import events
from . import handlers


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


HANDLERS: dict[type[events.Event], list[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
}
