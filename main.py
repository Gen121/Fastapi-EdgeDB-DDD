import functools
import edgedb
import uvicorn
from fastapi import Depends, FastAPI
from starlette.middleware.cors import CORSMiddleware

import pyd_model as model
import repository
from __init__ import get_edgedb_client


async def setup_edgedb(app):
    client = app.state.edgedb = edgedb.create_async_client()
    await client.ensure_connected()


async def shutdown_edgedb(app):
    client, app.state.edgedb = app.state.edgedb, None
    await client.aclose()


def make_app():
    app = FastAPI()

    app.on_event("startup")(functools.partial(setup_edgedb, app))
    app.on_event("shutdown")(functools.partial(shutdown_edgedb, app))

    @app.get("/health_check", include_in_schema=False)
    async def health_check() -> dict[str, str]:
        return {"status": "Ok"}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = make_app()


@app.get('/batch')
def get_batches(
    client: edgedb.Client = Depends(get_edgedb_client)
) -> model.Batch:
    repo = repository.EdgeDBRepository(client)
    return repo.get('batch1')


# @app.post('/allocate')
# def allocate_endpoint(
#     line: model.OrderLine,
#     client: edgedb.AsyncIOClient = Depends(get_edgedb_client)
# ) -> dict[str, str]:
#     repo = repository.EdgeDBRepository(client)
#     try:
#         batchref = services.allocate(line, repo, client)
#     except (model.OutOfStock, services.InvalidSku) as e:
#         return {"message": str(e)}, 400

#     return {"batchref": batchref}, 201


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
