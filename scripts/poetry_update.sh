#!/bin/bash

set -e

poetry update -vv --lock $@
