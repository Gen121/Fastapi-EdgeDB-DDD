import functools
from http import HTTPStatus
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from allocation.services import batch_services, unit_of_work
from allocation.adapters import pyd_model as model
from allocation.dbschema.config import setup_edgedb, shutdown_edgedb


def make_app(test_db: bool = False):
    app = FastAPI()

    app.on_event("startup")(functools.partial(setup_edgedb, app, test_db))
    app.on_event("shutdown")(functools.partial(shutdown_edgedb, app))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health_check")
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    @app.get('/batch')
    async def get_batch(
        uuid: UUID | None = None,
        reference: str | None = None,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> model.Batch:
        return await batch_services.get_batch(uow, uuid=uuid, reference=reference)

    @app.get('/batches')
    async def get_all_batches(
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> list[model.Batch]:
        return await batch_services.get_all(uow)

    @app.post('/allocate', status_code=HTTPStatus.CREATED)
    async def allocate_endpoint(
        line: model.OrderLine,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:
        try:
            batchref = await batch_services.allocate(
                **line.model_dump(), uow=uow)
        except (model.OutOfStock, batch_services.InvalidSku) as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"batchref": batchref}

    @app.post("/add_batch", status_code=HTTPStatus.CREATED)
    async def add_batch(
        batch: model.Batch,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:
        try:
            await batch_services.add_batch(
                **batch.model_dump(), uow=uow)
        except batch_services.OutOfStockInBatch as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"status": "Ok"}
    return app


app = make_app()
