import abc
import logging
from typing import Any, Awaitable, Callable

from allocation.domain import commands, events

from . import unit_of_work

logger = logging.getLogger(__name__)

AsyncEventHandler = Callable[..., Awaitable[Any | None]]
Message = commands.Command | events.Event


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
        while self.queue:
            message = self.queue.pop(0)
            match message:
                case events.Event():
                    await self.event_handler(message)
                case commands.Command():
                    await self.command_handler(message)
                case _:
                    raise Exception(f"{message} was not an Event or Command")

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
                logger.debug(f"handling event {event} with handler {handler}")
                await handler(event)
                events_list = [event async for event in self.uow.collect_new_events()]
                self.queue.extend(events_list)
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    async def command_handler(self, command: commands.Command):
        handler = self.command_handlers[type(command)]
        try:
            logger.debug(f"handling command {command}")
            await handler(command)
            events_list = [event async for event in self.uow.collect_new_events()]
            self.queue.extend(events_list)
        except Exception:
            logger.exception(
                "Exception handling command {command} with handler {handler}"
            )
            raise
