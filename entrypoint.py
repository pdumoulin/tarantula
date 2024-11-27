"""API entrypoint."""

import os

import uvicorn


if __name__ == '__main__':
    auto_reload = os.environ.get('AUTO_RELOAD', '').lower() == 'true'
    num_workers = int(os.environ.get('NUM_WORKERS', 3))
    uvicorn.run(
        'src.app:app',
        host='0.0.0.0',
        port=5000,
        reload=auto_reload,
        workers=num_workers
    )
