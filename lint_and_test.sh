#!/bin/bash

set -e

echo 'Running yamllint'
yamllint docker-compose.yaml

echo 'Running flake8'
flake8 src/ entrypoint.py

echo 'Running mypy'
mypy src/
