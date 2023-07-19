import uuid
from http import HTTPStatus

import pytest  # noqa
from httpx import AsyncClient

from allocation.dbschema import config


def random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def random_sku(name: str | int = "") -> str:
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name: str | int = "") -> str:
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name: str | int = "") -> str:
    return f"order-{name}-{random_suffix()}"


async def test_health_check(async_test_client):
    response = await async_test_client.get("/health_check")
    assert response.status_code == HTTPStatus.OK


async def post_to_add_batch(async_test_client, ref, sku, qty, eta):
    url = config.get_api_url()
    r = await async_test_client.post(
        f"{url}/add_batch", json={
            "reference": ref,
            "sku": sku,
            "purchased_quantity": qty,
            "eta": eta
            }
    )
    assert r.status_code == 201


@pytest.mark.usefixtures('restart_api')
async def test_api_returns_allocation(async_test_client: AsyncClient):
    sku, othersku = random_sku(), random_sku('other')
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    await post_to_add_batch(async_test_client, laterbatch, sku, 100, "2011-01-02")
    await post_to_add_batch(async_test_client, earlybatch, sku, 100, "2011-01-01")
    await post_to_add_batch(async_test_client, otherbatch, othersku, 100, None)
    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    req = await async_test_client.post(f'{url}/allocate', json=data)
    res = await async_test_client.get(f'{url}/batch', params={'reference': f'{earlybatch}'})
    assert req.status_code == 201
    assert req.json()['batchref'] == earlybatch
    assert data in res.json()['allocations']


@pytest.mark.usefixtures('restart_api')
async def test_unhappy_path_returns_400_and_error_message(async_test_client: AsyncClient):
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {'orderid': orderid, 'sku': unknown_sku, 'qty': 20}
    url = config.get_api_url()
    r = await async_test_client.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['detail'] == f'Invalid sku {unknown_sku}'


if __name__ == '__main__':
    pass
