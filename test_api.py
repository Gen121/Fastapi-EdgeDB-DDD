import uuid
from http import HTTPStatus
from fastapi import HTTPException

import pytest  # noqa
from fastapi.testclient import TestClient

from dbschema import config


def random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def random_sku(name: str | int = "") -> str:
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name: str | int = "") -> str:
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name: str | int = "") -> str:
    return f"order-{name}-{random_suffix()}"


async def test_health_check(test_client):
    response = test_client.get("/health_check")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures('restart_api')
async def test_api_returns_allocation(add_stock, test_client: TestClient):
    sku, othersku = random_sku(), random_sku('other')
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    await add_stock([
        (laterbatch, sku, 100, '2011-01-02'),
        (earlybatch, sku, 100, '2011-01-01'),
        (otherbatch, othersku, 100, '2011-12-12'),
    ])
    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}
    url = config.get_api_url()
    r = test_client.post(f'{url}/allocate', json=data)
    assert r.status_code == 201
    assert True
    assert r.json()['batchref'] == earlybatch


@pytest.mark.usefixtures('restart_api')
async def test_unhappy_path_returns_400_and_error_message(test_client: TestClient):
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {'orderid': orderid, 'sku': unknown_sku, 'qty': 20}
    url = config.get_api_url()
    r = test_client.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['detail'] == f'Invalid sku {unknown_sku}'


if __name__ == '__main__':
    pass