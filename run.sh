#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/home/pi/blinky
export PYTHONPATH=$PYTHONPATH:/home/pi/ir_tools
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

uwsgi \
    --http :1994 \
    --logto $DIR/logs/uwsgi.log \
    --pidfile $DIR/var/app.pid \
    --wsgi-file $DIR/web.py \
    --touch-reload $DIR/web.py
