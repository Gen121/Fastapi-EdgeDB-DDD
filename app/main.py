import functools
from http import HTTPStatus
from uuid import UUID

import edgedb
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

import repositories.repository as repository
import services.services as services
from __init__ import get_edgedb_client
from adapters import pyd_model as model
from dbschema import get_edgedb_dsn


async def setup_edgedb(app, test_db: bool = False):
    client = app.state.edgedb = edgedb.create_async_client(
        get_edgedb_dsn(test=test_db),
        tls_security='insecure'
    )
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


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

    @app.post('/allocate', status_code=HTTPStatus.CREATED)
    async def allocate_endpoint(
        line: model.OrderLine,
        async_client_db: edgedb.AsyncIOClient = Depends(get_edgedb_client)
    ) -> dict[str, str]:
        repo = repository.EdgeDBRepository(async_client_db)
        try:
            batchref = await services.allocate(
                **line.model_dump(), repo=repo, session=async_client_db)
        except (model.OutOfStock, services.InvalidSku) as e:
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.args[0])
        return {"batchref": batchref}

    return app


app = make_app()


@app.get('/batch')
async def get_batches(
    uuid: UUID | None = None,
    reference: str | None = None,
    async_client_db: edgedb.Client = Depends(get_edgedb_client)
) -> model.Batch | list[model.Batch]:
    repo = repository.EdgeDBRepository(async_client_db)
    return await repo.get(uuid=uuid, reference=reference)


@app.get('/batches')
async def get_all_batches(
    async_client_db: edgedb.Client = Depends(get_edgedb_client)
) -> list[model.Batch]:
    repo = repository.EdgeDBRepository(async_client_db)
    return await repo.list()


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
