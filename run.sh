#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/home/pi/blinky
export PYTHONPATH=$PYTHONPATH:/home/pi/ir-tools
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

uwsgi \
    --plugin python3 \
    --http-socket :1994 \
    --logto logs/uwsgi.log \
    --pidfile var/app.pid \
    --wsgi-file web.py \
    --touch-reload web.py

