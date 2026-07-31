import asyncio
import logging
from typing import Annotated, Union

import sentry_sdk
from fastapi import (
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    staticfiles,
    status,
    templating,
)
from pyblinky import AsyncWemo
from starlette.responses import Response as sResponse
from starlette.templating import _TemplateResponse as tResponse
from starlette.types import Scope as sScope

from src import config, constants, devices, models


class CacheControlledStaticFiles(staticfiles.StaticFiles):
    async def get_response(self, path: str, scope: sScope) -> sResponse:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = (
            f"public, max-age={config.STATIC_CACHE_TIME}"
        )
        return response


if config.ENVIRONMENT != constants.Environment.DEV or config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        environment=config.ENVIRONMENT.value,
        traces_sample_rate=1.0,
    )


def _reject_public(request: Request) -> None:
    if not request.client or request.client.host == config.PUBLIC_GATEWAY_IP:
        raise HTTPException(status_code=401)


app = config.TarantulaApp(lifespan=config.lifespan)
app.mount(
    f"/static/{config.STATIC_CACHE_KEY}",
    CacheControlledStaticFiles(directory="static"),
    name="static",
)

templates = templating.Jinja2Templates(directory="templates")


@app.exception_handler(devices.ChromecastRequestNotAllowed)
async def chromecast_conflict(
    request: Request, exc: devices.ChromecastRequestNotAllowed
) -> Response:
    return Response(status_code=status.HTTP_409_CONFLICT)


@app.get("/", include_in_schema=False)
async def root(request: Request) -> tResponse:
    return templates.TemplateResponse(
        request=request, name="root.html.jinja", context={"icon": "spider"}
    )


@app.get("/healthcheck")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/plugs", response_model=None)
async def get_plugs(
    request: Request, content_type: Annotated[str | None, Header()] = None
) -> Union[list[models.PlugResponse], tResponse]:
    if content_type != "application/json":
        return templates.TemplateResponse(
            request=request, name="plugs.html.jinja", context={"icon": "plug"}
        )

    active_plugs = app.state.plugs

    # gather data about current state
    results = await asyncio.gather(
        *([x.identify() for x in active_plugs] + [y.status() for y in active_plugs]),
        return_exceptions=True,
    )

    # handle missing data
    names = [
        str(x) if not isinstance(x, Exception) else "ERROR"
        for x in results[: len(results) // 2]
    ]
    statuses = [
        bool(x) if not isinstance(x, Exception) else None
        for x in results[len(results) // 2 :]
    ]
    indexes = range(0, len(active_plugs))

    # zip together data into model
    return [
        models.PlugResponse(id=index, name=name, status=status)
        for plug, name, status, index in zip(
            active_plugs, names, statuses, indexes, strict=True
        )
    ]


@app.patch("/plugs/{plug_id}")
async def post_plug(plug_id: int, body: models.PatchPlugBody) -> Response:
    try:
        plug = app.state.plugs[plug_id]
    except IndexError as e:
        raise HTTPException(status_code=404) from e
    if body.name is not None:
        await plug.rename(body.name)
    if body.status is not None:
        if body.status:
            await plug.on()
        else:
            await plug.off()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/chromecast", response_model=None, dependencies=[Depends(_reject_public)])
async def get_chromecast(
    request: Request, content_type: Annotated[str | None, Header()] = None
) -> Union[devices.ChromecastState, tResponse]:
    if content_type != "application/json":
        return templates.TemplateResponse(
            request=request,
            name="chromecast.html.jinja",
            context={"icon": "chromecast"},
        )
    return app.state.chromecast.get_state()


@app.post("/chromecast/start", dependencies=[Depends(_reject_public)])
async def post_start_chromecast(
    body: models.ChromecastStartBody,
) -> devices.ChromecastState:
    cc = app.state.chromecast
    return cc.start(body.url, body.mime_type)


@app.post("/chromecast/pause", dependencies=[Depends(_reject_public)])
async def post_pause_chromecast() -> devices.ChromecastState:
    cc = app.state.chromecast
    return cc.pause()


@app.post("/chromecast/play", dependencies=[Depends(_reject_public)])
async def post_play_chromecast() -> devices.ChromecastState:
    cc = app.state.chromecast
    return cc.play()


@app.post("/chromecast/seek", dependencies=[Depends(_reject_public)])
async def post_seek_chromecast(
    body: models.ChromecastSeekBody,
) -> devices.ChromecastState:
    cc = app.state.chromecast
    return cc.seek(body.time)


@app.post("/chromecast/seek_by", dependencies=[Depends(_reject_public)])
async def post_seek_by_chromecast(
    body: models.ChromecastSeekByBody,
) -> devices.ChromecastState:
    cc = app.state.chromecast
    return cc.seek_by(body.seconds)


@app.post("/chromecast/stop", dependencies=[Depends(_reject_public)])
async def post_stop_chromecast() -> devices.ChromecastState:
    cc = app.state.chromecast
    cc.stop()
    return devices.ChromecastState(
        playback_status=devices.ChromecastPlaybackStatus.UNKNOWN,
        duration=None,
        current_time=None,
        title=None,
        last_updated=None,
    )


@app.get("/remote", dependencies=[Depends(_reject_public)])
async def get_remote(request: Request) -> Response:
    buttons = [
        {"id": idx, "name": x.name} for idx, x in enumerate(app.state.remote.buttons)
    ]
    return templates.TemplateResponse(
        request=request,
        name="remote.html.jinja",
        context={"buttons": buttons, "icon": "tv"},
    )


@app.post("/remote/{button_id}", dependencies=[Depends(_reject_public)])
async def post_remote(button_id: int) -> Response:
    try:
        app.state.remote.press_button(button_id)
    except IndexError:
        raise HTTPException(status_code=404) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# GET in order to load on phone or watch browser easily
@app.get("/routines/{routine_name}", response_model=None)
async def run_routine(
    request: Request,
    routine_name: models.Routine,
    content_type: Annotated[str | None, Header()] = None,
) -> Union[Response, tResponse]:
    active_plugs = app.state.plugs

    # defaults
    on_plug_names = []
    off_plug_names = []
    icon = "spider"
    success = True

    try:
        # load plug names
        await asyncio.gather(*[x.identify() for x in active_plugs])

        # change variables based on routine
        if routine_name == models.Routine.BEDTIME:
            icon = "bedtime"
            on_plug_names = ["bedroom lamp"]
            off_plug_names = [
                "living room",
                "christmas tree",
                "goal",
                "patio lights",
                "downstairs ac",
            ]
        elif routine_name == models.Routine.SLEEPTIME:
            icon = "sleeptime"
            off_plug_names = [
                "living room",
                "christmas tree",
                "goal",
                "patio lights",
                "downstairs ac",
                "bedroom lamp",
            ]
        elif routine_name == models.Routine.WAKETIME:
            icon = "waketime"
            on_plug_names = ["living room", "christmas tree", "bedroom lamp"]
        else:
            raise NotImplementedError()

        # filter plugs based on configured names
        on_plugs = _filter_plugs(active_plugs, on_plug_names)
        off_plugs = _filter_plugs(active_plugs, off_plug_names)

        # perform actions
        await asyncio.gather(
            *([x.on() for x in on_plugs] + [y.off() for y in off_plugs])
        )
    except Exception:
        logging.exception(f"Exception in routine {routine_name}")
        success = False

    # return data
    if content_type == "application/json":
        if success:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise HTTPException(status_code=504)
    return templates.TemplateResponse(
        request=request,
        name="routines.html.jinja",
        context={"icon": icon, "name": routine_name.value.title(), "success": success},
    )


def _filter_plugs(plugs: list[AsyncWemo], names: list[str]) -> list[AsyncWemo]:
    return [
        plug for plug in plugs if any([name in plug._name.lower() for name in names])
    ]
