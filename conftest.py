# pytest: disable=redefined-outer-name
from datetime import date
import time
from pathlib import Path

import edgedb
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from dbschema import get_edgedb_dsn, get_api_url
from main import make_app


@pytest.fixture
def client_db() -> edgedb.Client:
    return edgedb.create_client(
        get_edgedb_dsn(test=True),
        tls_security='insecure'
    )


@pytest.fixture
def async_client_db() -> edgedb.AsyncIOClient:
    return edgedb.create_async_client(
        get_edgedb_dsn(test=True),
        tls_security='insecure'
    )


@pytest.fixture
async def async_client():
    async with AsyncClient(app=make_app(), base_url=get_api_url()) as client:
        yield client


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


@pytest.fixture
def restart_api():
    (Path(__file__).parent / "main.py").touch()
    time.sleep(0.3)


@pytest.fixture
async def add_stock(async_client_db: edgedb.AsyncIOClient):
    batches_added = set()
    skus_added = set()

    async def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            eta = date(*map(int, eta.split('-')))
            batch_id = await async_client_db.query_required_single(
                """Select(
                    INSERT Batch {
                        reference := <str>$reference,
                        sku := <str>$sku,
                        purchased_quantity := <int16>$purchased_quantity,
                        eta := <cal::local_date>$eta
                    }
                ){id}""",
                reference=ref, sku=sku, purchased_quantity=qty, eta=eta,
            )
            batches_added.add(batch_id.id)
            skus_added.add(sku)

    yield _add_stock

    await async_client_db.query(
        """DELETE OrderLine
            filter .sku in array_unpack(<array<str>>$data)
        """,
        data=list(skus_added)
    )

    await async_client_db.query(
        """DELETE Batch
            filter .id in array_unpack(<array<uuid>>$data)
        """,
        data=list(batches_added)
    )
