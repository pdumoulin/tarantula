#!/bin/bash

# /etc/rc.local setup (make sure system has exec and read or else reboot hangs)
# /home/pi/tarantule/run.sh & 

export PYTHONPATH=$PYTHONPATH:/home/pi/blinky
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

uwsgi \
    --http :1994 \
    --logto $DIR/logs/uwsgi.log \
    --pidfile $DIR/var/app.pid \
    --wsgi-file $DIR/web.py \
    --touch-reload $DIR/web.py
