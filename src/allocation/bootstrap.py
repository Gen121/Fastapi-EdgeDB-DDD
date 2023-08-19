import inspect
from typing import Callable

import edgedb
from fastapi import FastAPI, Request

from allocation.adapters import redis_eventpublisher
from allocation.adapters.notifications import AbstractNotifications, EmailNotifications
from allocation.app.settings import settings
from allocation.services import handlers, messagebus, unit_of_work


async def get_messagebus(request: Request) -> messagebus.MessageBus:
    return request.app.state.bus


def get_pull_connection_edgedb(test_db: bool = False) -> edgedb.AsyncIOClient:
    return edgedb.create_async_client(
        settings.get_edgedb_dsn(test_db=test_db), tls_security="insecure"
    )


def get_uow(
    async_client_db: edgedb.AsyncIOClient = get_pull_connection_edgedb(),
) -> unit_of_work.EdgedbUnitOfWork:
    return unit_of_work.EdgedbUnitOfWork(async_client_db)


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency for name, dependency in dependencies.items() if name in params
    }
    return lambda message: handler(message, **deps)


class Bootstrap:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork = get_uow(),
        notifications: AbstractNotifications = None,
        publish: Callable = redis_eventpublisher.publish,
    ):
        if not notifications:
            notifications = EmailNotifications()

        dependencies = {"uow": uow, "notifications": notifications, "publish": publish}
        injected_event_handlers = {
            event_type: [
                inject_dependencies(handler, dependencies) for handler in event_handlers
            ]
            for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
        }
        injected_command_handlers = {
            command_type: inject_dependencies(handler, dependencies)
            for command_type, handler in handlers.COMMAND_HANDLERS.items()
        }
        self.messagebus = messagebus.MessageBus(
            uow=uow,
            event_handlers=injected_event_handlers,
            command_handlers=injected_command_handlers,
        )

    async def __aenter__(self):
        return self.messagebus

    async def __aexit__(self, exc_type, exc, tb):
        await self.messagebus.uow.async_client.aclose()


bootstrap = Bootstrap()


async def aenter_lifespan(app: FastAPI):
    bus = app.state.bus = bootstrap.messagebus
    await bus.uow.async_client.ensure_connected()


async def aexit_lifespan(app: FastAPI):
    bus, app.state.bus = app.state.bus, None
    await bus.uow.async_client.aclose()
