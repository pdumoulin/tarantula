#!/bin/bash

set -e

# TODO move into npm container to run automatically
# npm install --save-dev --save-exact @biomejs/biome

biome lint static/
