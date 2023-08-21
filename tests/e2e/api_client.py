from http import HTTPStatus

from allocation.app.settings import settings

API_URL = settings.get_api_url()


async def post_to_add_batch(async_test_client, ref, sku, qty, eta):
    r = await async_test_client.post(
        f"{API_URL}/add_batch",
        json={"ref": ref, "sku": sku, "qty": qty, "eta": eta},
    )
    assert r.status_code == HTTPStatus.CREATED


async def post_to_allocate(async_test_client, orderid, sku, qty, expect_success=True):
    r = await async_test_client.post(
        f"{API_URL}/allocate",
        json={"orderid": orderid, "sku": sku, "qty": qty},
    )
    if expect_success:
        assert r.status_code == HTTPStatus.ACCEPTED
    return r


async def get_allocation(async_test_client, orderid):
    return await async_test_client.get(f"{API_URL}/allocations/{orderid}")
