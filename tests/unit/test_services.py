import pytest
import domain.model as model
import repositories.repository as repository
import services.services as services


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


async def test_returns_allocation():
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = repository.FakeRepository([batch])

    result = await services.allocate(
        orderid="o1", sku="COMPLICATED-LAMP", qty=10,
        repo=repo, session=FakeSession()
    )
    assert result == "b1"


async def test_error_for_invalid_sku():
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = repository.FakeRepository([batch])

    try:
        await services.allocate(
            orderid="o1", sku="NONEXISTENTSKU", qty=10,
            repo=repo, session=FakeSession()
        )
    except services.InvalidSku as e:
        with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e
