import json
import pytest
from tenacity import AsyncRetrying, RetryError, stop_after_delay
from . import api_client, redis_client


@pytest.mark.usefixtures("async_client_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_redis_pubsub")
async def test_change_batch_quantity_leading_to_reallocation(
    async_test_client, random_batchref, random_orderid, random_sku
):
    # start with two batches and an order allocated to one of them
    orderid, sku = random_orderid(), random_sku()
    earlier_batch, later_batch = random_batchref("old"), random_batchref("newer")
    await api_client.post_to_add_batch(async_test_client, earlier_batch, sku, qty=10, eta="2011-01-01")
    await api_client.post_to_add_batch(async_test_client, later_batch, sku, qty=10, eta="2011-01-02")
    response = await api_client.post_to_allocate(async_test_client, orderid, sku, 10)
    assert response.json()["batchref"] == earlier_batch

    subscription = await redis_client.subscribe_to("line_allocated")

    # change quantity on allocated batch so it's less than our order
    await redis_client.publish_message(
        "change_batch_quantity",
        {"batchref": earlier_batch, "qty": 5},
    )

    # wait until we see a message saying the order has been reallocated
    messages = []
    async for attempt in AsyncRetrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = await subscription.get_message(timeout=1)
            print(messages)
            if message:
                messages.append(message)
                print(messages)
            data = json.loads(messages[-1]["data"])
            assert data["orderid"] == orderid
            assert data["batchref"] == later_batch
