import os

from dotenv import load_dotenv

load_dotenv('.env')


def get_edgedb_dsn(*, test: bool = False) -> str:
    host = os.environ.get('APP_NAME', 'localhost')
    port = os.environ.get('EDGEDB_PORT', 5656)
    password = os.environ.get("APP_NAME", None)
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


if __name__ == '__main__':
    print(get_edgedb_dsn())
# (#!/bin/sh or #!/bin/bash)
