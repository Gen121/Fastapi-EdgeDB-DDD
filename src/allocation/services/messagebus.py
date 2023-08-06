import abc
from typing import Any, Awaitable, Callable

from allocation.domain import events
from . import handlers, unit_of_work

AsyncEventHandler = Callable[..., Awaitable[Any | None]]


class AbstractMessageBus(abc.ABC):
    HANDLERS: dict[type[events.Event], list[AsyncEventHandler]]
    results: list = []

    async def handle(self, event: events.Event):
        for handler in self.HANDLERS[type(event)]:
            self.results.append(await handler(event=event, uow=uow))
            list_of_event = []
            async for event in uow.collect_new_events():
                list_of_event.append(event)
            queue.extend(list_of_event)


async def handle(
    event: events.Event,
    uow: unit_of_work.AbstractUnitOfWork,
):
    queue = [event]
    results = []
    while queue:
        print(queue)
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(await handler(event=event, uow=uow))
            list_of_event = []
            async for event in uow.collect_new_events():
                list_of_event.append(event)
            queue.extend(list_of_event)
    return results


HANDLERS: dict[type[events.Event], list[AsyncEventHandler]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
}
