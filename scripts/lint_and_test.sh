#!/bin/bash

set -e

echo 'Running yamllint'
yamllint docker-compose.yaml

echo 'Running ruff'
ruff check src/ --no-cache --select I,F,E,W,B
ruff format src/ --diff --no-cache

echo 'Running mypy'
mypy --disallow-untyped-defs --cache-dir=/dev/null src
