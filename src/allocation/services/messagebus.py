import abc
import logging
from typing import Any, Awaitable, Callable

from fastapi import Depends

from allocation.domain import commands, events

from . import handlers, unit_of_work

logger = logging.getLogger(__name__)

AsyncEventHandler = Callable[..., Awaitable[Any | None]]
Message = commands.Command | events.Event

EVENT_HANDLERS: dict[type[events.Event], list[AsyncEventHandler]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.Allocated: [handlers.publish_allocated_event]
}

COMMAND_HANDLERS: dict[type[commands.Command], AsyncEventHandler] = {
    commands.CreateBatch: handlers.add_batch,
    commands.Allocate: handlers.allocate,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}


class AbstractMessageBus(abc.ABC):
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: dict[type[events.Event], list[AsyncEventHandler]],
        command_handlers: dict[type[commands.Command], AsyncEventHandler],
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    async def handle(self, message: Message):
        self.queue = [message]
        self.results: list = []
        while self.queue:
            message = self.queue.pop(0)
            match message:
                case events.Event():
                    await self.event_handler(message)
                case commands.Command():
                    await self.command_handler(message)
                case _:
                    raise Exception(f"{message} was not an Event or Command")
        return self.results

    @abc.abstractmethod
    async def event_handler(self, event: events.Event):
        pass

    @abc.abstractmethod
    async def command_handler(self, command: commands.Command):
        pass


class MessageBus(AbstractMessageBus):
    async def event_handler(self, event: events.Event):
        for handler in self.event_handlers[type(event)]:
            try:
                self.results.append(await handler(event=event, uow=self.uow))
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue
            list_of_event = []
            async for event in self.uow.collect_new_events():
                if not event:
                    continue
                list_of_event.append(event)
            self.queue.extend(list_of_event)

    async def command_handler(self, command: commands.Command):
        handler = self.command_handlers[type(command)]
        try:
            self.results.append(await handler(cmd=command, uow=self.uow))
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
        list_of_event = []
        async for command in self.uow.collect_new_events():
            if not command:
                continue
            list_of_event.append(command)
        self.queue.extend(list_of_event)


async def get_messagebus(unit_of_work: unit_of_work.AbstractUnitOfWork = Depends(unit_of_work.get_uow)) -> MessageBus:
    return MessageBus(unit_of_work, EVENT_HANDLERS, COMMAND_HANDLERS)
