#!/bin/bash

set -e

mkdir -p logs

echo STATIC_CACHE_KEY=$(git log -1 --pretty=format:%H -- static) > .env

docker compose build deploy

docker compose down deploy

docker compose up -d deploy
