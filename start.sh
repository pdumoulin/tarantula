#!/bin/bash

set -e

mkdir -p logs

echo STATIC_CACHE_KEY=$(git rev-parse HEAD) > .env

docker compose down deploy

docker compose up --build -d deploy
