"""App entrypoint."""

import asyncio
from typing import Annotated

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Header
from fastapi import Request
from fastapi import Response
from fastapi import staticfiles
from fastapi import status
from fastapi import templating

from pyblinky import AsyncWemo

from starlette.responses import Response as sResponse
from starlette.types import Scope as sScope

from src import config
from src import models


class CacheControlledStaticFiles(staticfiles.StaticFiles):
    """Cached static files."""

    async def get_response(self, path: str, scope: sScope) -> sResponse:
        """Add response headers for browser caching."""
        response = await super().get_response(path, scope)
        response.headers['Cache-Control'] = \
            f'public, max-age={config.STATIC_CACHE_TIME}'
        return response


app = FastAPI(lifespan=config.lifespan)
app.mount(
    '/static', CacheControlledStaticFiles(directory='static'), name='static')

templates = templating.Jinja2Templates(directory='templates')


@app.get('/healthcheck')
async def healthcheck():
    """App up check."""
    return {'status': 'ok'}


@app.get('/switches')  # backwards compatible
@app.get('/plugs')
async def get_plugs(
        request: Request,
        content_type: Annotated[str | None, Header()] = None
        ) -> list[models.PlugResponse]:
    """Fetch current status of plugs."""
    plugs = app.state.plugs

    # filter out plugs that are not active
    active_plugs = [x for x in plugs if x]

    # gather data about current state
    results = await asyncio.gather(
        *(
            [
                x.identify()
                for x in active_plugs
            ] +
            [
                y.status()
                for y in active_plugs
            ]
        )
    )

    # handle missing data
    names = [
        x if not isinstance(x, Exception) else 'ERROR'
        for x in results[:len(results)//2]
    ]
    statuses = [
        x if not isinstance(x, Exception) else None
        for x in results[len(results)//2:]
    ]
    indexes = [
        x
        for x in range(0, len(plugs))
        if plugs[x]
    ]

    # zip together data into model
    return_plugs = [
        models.PlugResponse(
            id=index,
            ip=plug.ip,
            name=name,
            status=status
        )
        for plug, name, status, index
        in zip(active_plugs, names, statuses, indexes)
    ]

    # return data
    if content_type == 'application/json':
        return return_plugs
    return templates.TemplateResponse(
        request=request,
        name='plugs.html',
        context={
            'plugs': return_plugs
        }
    )


def _find_plug(index: int) -> AsyncWemo:
    """Get plug from app state."""
    plug = None
    try:
        plug = app.state.plugs[index]
    except IndexError:
        pass

    # inactive plug or invalid index
    if not plug:
        raise HTTPException(status_code=404)
    return plug


@app.patch('/plugs/{plug_id}')
async def post_plug(
        plug_id: int,
        body: models.PatchPlugBody):
    """Post plug actions."""
    plug = _find_plug(plug_id)
    if body.name is not None:
        await plug.rename(body.name)
    if body.status is not None:
        if body.status:
            await plug.on()
        else:
            await plug.off()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get('/remote')
async def get_remote(request: Request):
    """Display remote."""
    buttons = [
        {
            'id': idx,
            'name': x.name
        }
        for idx, x in enumerate(app.state.remote.buttons)
    ]
    return templates.TemplateResponse(
        request=request,
        name='remote.html',
        context={
            'buttons': buttons
        }
    )


@app.post('/remote/{button_id}')
async def post_remote(button_id: int):
    """Button press on remote."""
    try:
        app.state.remote.press_button(button_id)
    except IndexError:
        raise HTTPException(status_code=404)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# TODO - endpoint for routines

# TODO - update README.md and service start config
