import asyncio
import csv
import os
import tempfile

import uvicorn
from pyblinky import AsyncWemo

from src import config


async def main() -> None:
    auto_reload = os.environ.get("AUTO_RELOAD", "").lower() == "true"
    num_workers = int(os.environ.get("NUM_WORKERS", 3))

    # determine active plugs before worker forking
    plugs = [AsyncWemo(ip) for ip in config.PLUG_IPS]
    results = await asyncio.gather(
        *[plug.identify() for plug in plugs], return_exceptions=True
    )
    active_plugs = [
        {"ip": plug.ip, "name": result}
        for plug, result in zip(plugs, results, strict=True)
        if not isinstance(result, Exception)
    ]

    # write to file for each worker to read
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False
    ) as tmpfile:
        writer = csv.DictWriter(tmpfile, fieldnames=["ip", "name"])
        writer.writeheader()
        writer.writerows(active_plugs)
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
