# pytest: disable=redefined-outer-name
import pytest
import edgedb


@pytest.fixture
def client():
    return edgedb.create_client()
