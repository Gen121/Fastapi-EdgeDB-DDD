import functools
from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from allocation.domain import events
from allocation.dbschema.config import setup_edgedb, shutdown_edgedb
from allocation.services import unit_of_work, messagebus, handlers


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

    @app.post("/add_batch", status_code=HTTPStatus.CREATED)
    async def add_batch(
        batch: events.BatchCreated,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:

        # if batch.eta is not None:
        #     batch.eta = datetime.datetime.fromisoformat(batch.eta).date()

        await messagebus.handle(batch, uow=uow)
        return {"status": "Ok"}

    @app.post('/allocate', status_code=HTTPStatus.CREATED)
    async def allocate_endpoint(
        line: events.AllocationRequired,
        uow: unit_of_work.EdgedbUnitOfWork = Depends(unit_of_work.get_uow)
    ) -> dict[str, str]:
        try:
            batchref = await messagebus.handle(line, uow=uow)
        except handlers.InvalidSku as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"batchref": batchref[0]}

    return app


app = make_app()
