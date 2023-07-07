import os

from dotenv import load_dotenv

load_dotenv('.env')


def get_edgedb_dsn(*, test: bool = False) -> str:
    host = os.environ.get('EDGEDB_HOST', 'localhost')
    port = os.environ.get('EDGEDB_PORT', 5656)
    password = os.environ.get("EDGEDB_PASSWORD", None)
    user = os.environ.get("EDGEDB_USER", "edgedb")
    db_name = (
        os.environ.get("EDGEDB_DATABASE", "edgedb") if not test
        else "test_db"
    )
    return f'edgedb://{user}:{password}@{host}:{port}/{db_name}'


def get_api_url() -> str:
    host = os.environ.get("API_HOST", "localhost")
    port = os.environ.get("API_PORT", "8000")
    return f"http://{host}:{port}"
