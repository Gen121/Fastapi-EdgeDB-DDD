import pytest
import domain.model as model
import repositories.repository as repository
import services.services as services


class FakeRepository(repository.AbstractRepository):
    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        return FakeRepository([model.Batch(ref, sku, qty, eta), ])

    def __init__(self, batches):
        self._batches = set(batches)

    async def add(self, batch):
        self._batches.add(batch)

    async def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    async def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


async def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    await services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get(reference="b1") is not None


async def test_returns_allocation():
    repo = FakeRepository.for_batch("b1", "COMPLICATED-LAMP", 100, eta=None)

    result = await services.allocate(
        orderid="o1", sku="COMPLICATED-LAMP", qty=10,
        repo=repo, session=FakeSession()
    )
    assert result == "b1"


async def test_error_for_invalid_sku():
    repo = FakeRepository.for_batch("b1", "AREALSKU", 100, eta=None)

    try:
        await services.allocate(
            orderid="o1", sku="NONEXISTENTSKU", qty=10,
            repo=repo, session=FakeSession()
        )
    except services.InvalidSku as e:
        with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            raise e
