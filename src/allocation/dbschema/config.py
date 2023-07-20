from fastapi import Request
import edgedb
from allocation.app.settings import settings


async def get_edgedb_client(request: Request) -> edgedb.AsyncIOClient:
    return request.app.state.edgedb


async def setup_edgedb(app, test_db: bool = False):
    client = app.state.edgedb = edgedb.create_async_client(
        settings.get_edgedb_dsn(test_db=test_db),
        tls_security='insecure'
    )
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


if __name__ == '__main__':
    print(settings.get_edgedb_dsn())
