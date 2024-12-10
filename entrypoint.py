"""API entrypoint."""

import asyncio
import os

from pyblinky import AsyncWemo

import uvicorn

from src import config


async def main():
    """App entrypoint."""
    auto_reload = os.environ.get('AUTO_RELOAD', '').lower() == 'true'
    num_workers = int(os.environ.get('NUM_WORKERS', 3))

    # determine active plugs before worker forking
    plugs = [
        AsyncWemo(ip)
        for ip in config.PLUG_IPS
    ]
    results = await asyncio.gather(
        *[
            plug.identify()
            for plug in plugs
        ],
        return_exceptions=True
    )
    active_plug_ips = [
        plug.ip
        for plug, result in zip(plugs, results)
        if not isinstance(result, Exception)
    ]
    os.environ['ACTIVE_PLUG_IPS'] = ','.join(active_plug_ips)

    uvicorn.run(
        'src.app:app',
        host='0.0.0.0',
        port=5000,
        reload=auto_reload,
        workers=num_workers
    )

if __name__ == '__main__':
    asyncio.run(main())
