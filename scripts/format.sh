#!/bin/bash

set -e

echo 'Running ruff/isort'
ruff check --select I --fix .

echo 'Running ruff'
ruff format src/
