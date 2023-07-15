import os

from fastapi import Request
from dotenv import load_dotenv
import edgedb
load_dotenv('.env')


def get_edgedb_dsn(*, test: bool = False) -> str:
    host = os.environ.get('APP_NAME', 'localhost')
    # host = "localhost"
    port = os.environ.get('EDGEDB_PORT', 5656)
    # port = 10704
    password = os.environ.get("APP_NAME", None)
    # password = "cB2pjoYWCudiwVryOmXP2YhL"
    user = os.environ.get("EDGEDB_SERVER_USER", "edgedb")
    db_name = (
        os.environ.get("EDGEDB_DATABASE", "edgedb") if not test
        else "edgedb"
    )
    return f'edgedb://{user}:{password}@{host}:{port}/{db_name}'


def get_api_url() -> str:
    host = os.environ.get("API_HOST", "localhost")
    port = os.environ.get("API_PORT", "5005")
    return f"http://{host}:{port}"


async def get_edgedb_client(request: Request) -> edgedb.AsyncIOClient:
    return request.app.state.edgedb


async def setup_edgedb(app, test_db: bool = False):
    client = app.state.edgedb = edgedb.create_async_client(
        get_edgedb_dsn(test=test_db),
        tls_security='insecure'
    )
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


if __name__ == '__main__':
    print(get_edgedb_dsn())
