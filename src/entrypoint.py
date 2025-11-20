import asyncio
import os
import pickle
import tempfile

import uvicorn
from pyblinky import AsyncWemo

from src import config
from src.devices import Remote


async def main() -> None:
    auto_reload = os.environ.get("AUTO_RELOAD", "").lower() == "true"
    num_workers = int(os.environ.get("NUM_WORKERS", 3))

    # discover and auth remote
    remote = Remote(config.IR_EMITTER_IP, config.REMOTE_BUTTONS)

    # determine active plugs before worker forking
    plugs = [
        AsyncWemo(ip, name_cache_age=config.PLUG_CACHE_NAME_TIME)
        for ip in config.PLUG_IPS
    ]
    results = await asyncio.gather(
        *[plug.identify() for plug in plugs], return_exceptions=True
    )

    # pickle objects for each worker to grab
    dynamic_config = {
        "plugs": [
            plug
            for plug, result in zip(plugs, results, strict=True)
            if not isinstance(result, Exception)
        ],
        "remote": remote,
    }
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmpfile:
        pickle.dump(dynamic_config, tmpfile)
        os.environ["DYNAMIC_CONFIG_FILENAME"] = tmpfile.name

    # start app with workers
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=5000,
        reload=auto_reload,
        workers=num_workers,
        log_config="log.ini",
    )


if __name__ == "__main__":
    asyncio.run(main())
