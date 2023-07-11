# pytest: disable=redefined-outer-name
import time
from http import HTTPStatus
from pathlib import Path

import edgedb
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from allocation.app.main import make_app
from allocation.dbschema import get_api_url, get_edgedb_dsn


async def wait_for_edgedb_to_come_up(async_client_db: edgedb.AsyncIOClient):
    deadline = time.time() + 10
    message = ''
    while time.time() < deadline:
        try:
            await async_client_db.ensure_connected()
        except Exception as e:
            message = str(e)
            time.sleep(0.5)
        else:
            return
    pytest.exit(f"Edgedb never came up: {message}", returncode=1)


@pytest.fixture
async def async_client_db() -> edgedb.AsyncIOClient:
    async_client_db = edgedb.create_async_client(
        get_edgedb_dsn(test=True),
        tls_security='insecure'
    )
    await wait_for_edgedb_to_come_up(async_client_db)
    return async_client_db


@pytest.fixture
async def async_test_client(async_client_db: edgedb.AsyncIOClient):
    app = make_app()
    app.state.edgedb = async_client_db
    async with AsyncClient(app=app, base_url=get_api_url()) as client:
        yield client
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


@pytest.fixture
def test_client():
    with TestClient(make_app(test_db=True)) as client:
        yield client


@pytest.fixture
def tx_test_client(mocker):
    mocker.patch("app.main.setup_edgedb", tx_setup_edgedb)
    mocker.patch("app.main.shutdown_edgedb", tx_shutdown_edgedb)
    with TestClient(make_app()) as client:
        yield client


async def tx_setup_edgedb(app):
    client = app.state.edgedb_client = edgedb.create_async_client(
        get_edgedb_dsn(test=True),
        tls_security='insecure'
    )
    await client.ensure_connected()
    async for tx in client.with_retry_options(edgedb.RetryOptions(0)).transaction():
        await tx.__aenter__()
        app.state.edgedb = tx
        break


async def tx_shutdown_edgedb(app):
    client, app.state.edgedb_client = app.state.edgedb_client, None
    tx, app.state.edgedb = app.state.edgedb, None
    await tx.__aexit__(Exception, Exception(), None)
    await client.aclose()


async def wait_for_webapp_to_come_up(async_test_client: AsyncClient):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            response = await async_test_client.get("/health_check")
            assert response.status_code == HTTPStatus.OK
        except Exception:
            time.sleep(0.5)
        else:
            return
    pytest.exit("API never came up", returncode=1)


@pytest.fixture
async def restart_api(async_test_client):
    (Path(__file__).parent.parent / "src" / "allocation" / "app" / "main.py").touch()
    time.sleep(0.5)
    await wait_for_webapp_to_come_up(async_test_client)
