# pytest: disable=redefined-outer-name
import pytest
import edgedb
from fastapi.testclient import TestClient

from main import make_app
from dbschema import get_edgedb_dsn


@pytest.fixture
def client() -> edgedb.Client:
    return edgedb.create_client(
        get_edgedb_dsn(test=True),
        tls_security='insecure'
    )


@pytest.fixture
def test_client():
    with TestClient(make_app()) as client:
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
