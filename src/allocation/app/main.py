import functools
from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from allocation.adapters import pyd_model as model
from allocation.dbschema.config import setup_edgedb, shutdown_edgedb
from allocation.services import handlers, unit_of_work


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

    @app.get('/product')
    async def get_product(
        sku: str,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> model.Product | None:
        return await handlers.get(uow, sku=sku)

    @app.get('/batches')
    async def get_all_batches(
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> list[model.Batch]:
        return await handlers.get_all(uow)

    @app.post('/allocate', status_code=HTTPStatus.CREATED)
    async def allocate_endpoint(
        line: model.OrderLine,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:
        try:
            batchref = await handlers.allocate(
                **line.model_dump(), uow=uow)
        except handlers.InvalidSku as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"batchref": batchref}

    @app.post("/add_batch", status_code=HTTPStatus.CREATED)
    async def add_batch(
        batch: model.Batch,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:
        if batch.allocations:
            batch.allocations = list(batch.allocations)
        try:
            await handlers.add_batch(
                **batch.model_dump(), uow=uow)
        except handlers.OutOfStockInBatch as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"status": "Ok"}
    return app


app = make_app()
