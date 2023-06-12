# pytest: disable=redefined-outer-name
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_tables import metadata
import edgedb

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    yield sessionmaker(bind=in_memory_db)()


@pytest.fixture
def client():
    return edgedb.create_client()

