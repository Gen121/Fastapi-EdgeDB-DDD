from datetime import date

import pytest
from unittest import mock

from allocation import bootstrap, views
from allocation.domain import commands
from allocation.services import unit_of_work

today = date.today()


@pytest.fixture
def messagebus(async_client_db):
    yield bootstrap.Bootstrap(
        uow=unit_of_work.EdgedbUnitOfWork(async_client_db),
        notifications=mock.Mock(),
        publish=lambda *args: None,
    ).messagebus


async def test_allocations_view(messagebus, random_batchref, random_sku, random_orderid):
    orderid, orderid_other = random_orderid("order1"), random_orderid("otherorder")
    sku_1, sku_2 = (
        random_sku("sku1"),
        random_sku("sku2"),
    )
    batchref_1, batchref_2, batchref_1_later = (
        random_batchref("sku1"),
        random_batchref("sku2"),
        random_batchref("sku1batch-later"),
    )
    await messagebus.handle(commands.CreateBatch(batchref_1, sku_1, 50, None))
    await messagebus.handle(commands.CreateBatch(batchref_2, sku_2, 50, today))
    await messagebus.handle(commands.Allocate(orderid, sku_1, 20))
    await messagebus.handle(commands.Allocate(orderid, sku_2, 20))
    # add a spurious batch and order to make sure we're getting the right ones
    await messagebus.handle(commands.CreateBatch(batchref_1_later, sku_1, 50, today))
    await messagebus.handle(commands.Allocate(orderid_other, sku_1, 30))
    await messagebus.handle(commands.Allocate(orderid_other, sku_2, 10))
    assert await views.allocations(orderid, messagebus.uow) == [
        {"sku": sku_1, "batchref": batchref_1},
        {"sku": sku_2, "batchref": batchref_2},
    ]


async def test_deallocation(messagebus, random_batchref, random_sku, random_orderid):
    sku = random_sku("sku1")
    orderid = random_orderid()
    batchref_1, batchref_2 = (
        random_batchref("sku1"),
        random_batchref("sku2"),
    )
    await messagebus.handle(commands.CreateBatch(batchref_1, sku, 50, None))
    await messagebus.handle(commands.CreateBatch(batchref_2, sku, 50, today))
    await messagebus.handle(commands.Allocate(orderid, sku, 40))
    await messagebus.handle(commands.ChangeBatchQuantity(batchref_1, 10))

    assert await views.allocations(orderid, messagebus.uow) == [
        {"sku": sku, "batchref": batchref_2},
    ]
