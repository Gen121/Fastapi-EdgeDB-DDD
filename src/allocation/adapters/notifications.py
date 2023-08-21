# pylint: disable=too-few-public-methods
import abc

import aiosmtplib

from allocation.app.settings import settings


class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    async def send(self, destination, message):
        raise NotImplementedError


DEFAULT_HOST = settings.get_email_host_and_port()["host"]
DEFAULT_PORT = settings.get_email_host_and_port()["port"]


class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = aiosmtplib.SMTP(smtp_host, port=port)

    async def send(self, destination, message):
        msg = f"Subject: allocation service notification\n{message}"
        await self.server.sendmail(
            from_addr="allocations@example.com",
            to_addrs=[destination],
            msg=msg,
        )
