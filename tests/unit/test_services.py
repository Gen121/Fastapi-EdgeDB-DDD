import pytest
import domain.model as model
import repositories.repository as repository
import services.services as services


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


async def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = repository.FakeRepository([batch])

    result = await services.allocate(line, repo, FakeSession())
    assert result == "b1"


async def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = repository.FakeRepository([batch])

    try:
        await services.allocate(line, repo, FakeSession())
    except services.InvalidSku as e:
        with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e
