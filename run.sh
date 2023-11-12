#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/home/pi/projects/blinky
export PYTHONPATH=$PYTHONPATH:/home/pi/projects/ir-tools
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR

uwsgi \
    --plugin python3 \
    --http-socket :1994 \
    --logto logs/uwsgi.log \
    --pidfile var/app.pid \
    --wsgi-file web.py \
    --processes 6 \
    --enable-threads \
    --touch-reload web.py
