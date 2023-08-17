import functools
from http import HTTPStatus

from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from allocation import bootstrap, views
from allocation.domain import commands
from allocation.services import handlers


def make_app(test_db: bool = False):
    app = FastAPI()

    messagebus = bootstrap.bootstrap.messagebus
    app.on_event("startup")(functools.partial(bootstrap.aenter_lifespan, app))
    app.on_event("shutdown")(functools.partial(bootstrap.aexit_lifespan, app))

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
    async def add_batch(batch: commands.CreateBatch) -> dict[str, str]:
        # if batch.eta is not None:  # TODO: вынести в валидаторы
        #     batch.eta = datetime.datetime.fromisoformat(batch.eta).date()
        await messagebus.handle(batch)
        return {"status": "Ok"}

    @app.post("/allocate", status_code=HTTPStatus.ACCEPTED)
    async def allocate_endpoint(line: commands.Allocate) -> dict[str, str]:
        try:
            await messagebus.handle(line)
        except handlers.InvalidSku as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"status": "Ok"}

    @app.get("/allocations/{orderid}", status_code=HTTPStatus.OK)
    async def allocations_view_endpoint(orderid: str):
        result = await views.allocations(orderid, messagebus.uow)
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND, detail="not found")
        return result

    return app


app = make_app()
