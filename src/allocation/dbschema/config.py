import os
import random

from fastapi import Request
from dotenv import load_dotenv
import edgedb
if env := load_dotenv('.venv') is not True:
    load_dotenv('/.venv')


def ttest() -> str:
    return str(os.environ.get("TEST", f"NoN{random.randint(0, 999)}"))


def get_edgedb_dsn(*, test: bool = False) -> str:
    host = os.environ.get('DB_HOSTNAME')
    port = os.environ.get('DB_PORT')
    password = os.environ.get("DB_ROOT_PASSWORD")
    user = os.environ.get("DB_USER_NAME")
    db_name = (
        os.environ.get("DB_NAME") if not test
        else os.environ.get("DB_TEST_NAME")
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
