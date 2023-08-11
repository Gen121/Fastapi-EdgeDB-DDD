from datetime import date
from allocation import views
from allocation.domain import commands
from allocation.services import unit_of_work
from allocation.services.messagebus import get_messagebus

today = date.today()


async def test_allocations_view(async_client_db, random_batchref, random_sku, random_orderid):
    uow = unit_of_work.EdgedbUnitOfWork(async_client_db)
    messagebus = await get_messagebus(uow)
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
    assert await views.allocations(orderid, uow) == [
        {"sku": sku_1, "batchref": batchref_1},
        {"sku": sku_2, "batchref": batchref_2},
    ]
