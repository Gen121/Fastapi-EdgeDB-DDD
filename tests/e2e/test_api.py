from http import HTTPStatus

import pytest

from allocation.app.settings import settings
from tests.e2e.api_client import post_to_add_batch, post_to_allocate


API_URL = settings.get_api_url()


async def test_health_check(async_test_client):
    response = await async_test_client.get("/health_check")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("restart_api")
async def test_api_returns_allocation(async_test_client, random_batchref, random_orderid, random_sku):
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref("_1")
    laterbatch = random_batchref("_2")
    otherbatch = random_batchref("_3")
    await post_to_add_batch(async_test_client, laterbatch, sku, 100, "2011-01-02")
    await post_to_add_batch(async_test_client, earlybatch, sku, 100, "2011-01-01")
    await post_to_add_batch(async_test_client, otherbatch, othersku, 100, None)
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    req = await async_test_client.post(f"{API_URL}/allocate", json=data)
    assert req.status_code == 201
    assert req.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
async def test_unhappy_path_returns_400_and_error_message(async_test_client, random_orderid, random_sku):
    unknown_sku, orderid = random_sku(), random_orderid()
    r = await post_to_allocate(async_test_client, orderid, unknown_sku, 20, False)
    assert r.status_code == 400
    assert r.json()["detail"] == f"Invalid sku {unknown_sku}"
