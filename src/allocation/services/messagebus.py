from typing import Callable

from allocation.adapters import email
from allocation.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


HANDLERS: dict[type[events.Event], list[Callable]] = {
    events.OutOfStock: [send_out_of_stock_notification],
}
