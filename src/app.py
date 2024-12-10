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
    f'/static/{config.STATIC_CACHE_KEY}',
    CacheControlledStaticFiles(directory='static'),
    name='static')

templates = templating.Jinja2Templates(directory='templates')


@app.get('/', include_in_schema=False)
async def root(request: Request):
    """App root with metadata."""
    return templates.TemplateResponse(
        request=request,
        name='root.html.jinja',
        context={'icon': 'spider'}
    )


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
        ),
        return_exceptions=True
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
        name='plugs.html.jinja',
        context={
            'plugs': return_plugs,
            'icon': 'plug'
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
        name='remote.html.jinja',
        context={
            'buttons': buttons,
            'icon': 'tv'
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


# GET in order to load on phone or watch browser easily
@app.get('/routines/{routine_name}')
async def run_routine(
        request: Request,
        routine_name: models.Routine,
        content_type: Annotated[str | None, Header()] = None
        ):
    """Execute a routine."""
    plugs = app.state.plugs

    # defaults
    on_plug_names = []
    off_plug_names = []
    icon = 'spider'
    success = True

    try:
        # filter out plugs that are not active
        active_plugs = [x for x in plugs if x]

        # load plug names
        await asyncio.gather(
            *[
                x.identify()
                for x in active_plugs
            ]
        )

        # change variables based on routine
        if routine_name == models.Routine.BEDTIME:
            icon = 'bedtime'
            on_plug_names = [
                'bedroom lamp'
            ]
            off_plug_names = [
                'living room',
                'christmas tree',
                'goal',
                'patio lights',
                'downstairs ac'
            ]
        elif routine_name == models.Routine.SLEEPTIME:
            icon = 'sleeptime'
            off_plug_names = [
                'living room',
                'christmas tree',
                'goal',
                'patio lights',
                'downstairs ac',
                'bedroom lamp'
            ]
        elif routine_name == models.Routine.WAKETIME:
            icon = 'waketime'
            on_plug_names = [
                'living room',
                'christmas tree',
                'bedroom lamp'
            ]
        else:
            raise NotImplementedError()

        # filter plugs based on configured names
        on_plugs = _filter_plugs(active_plugs, on_plug_names)
        off_plugs = _filter_plugs(active_plugs, off_plug_names)

        # perform actions
        await asyncio.gather(
            *(
                [
                    x.on()
                    for x in on_plugs
                ] +
                [
                    y.off()
                    for y in off_plugs
                ]

            )
        )
    except Exception:
        # TODO - logging of stack traces
        success = False

    # return data
    if content_type == 'application/json':
        if success:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException(status_code=504)
    return templates.TemplateResponse(
        request=request,
        name='routines.html.jinja',
        context={
            'icon': icon,
            'name': routine_name.value.title(),
            'success': success
        }
    )


def _filter_plugs(plugs: list[AsyncWemo], names: list[str]):
    """Filter list of plugs containing matches from list of names."""
    return [
        plug
        for plug in plugs
        if any(
            [
                name in plug._name.lower()
                for name in names
            ]
        )
    ]
