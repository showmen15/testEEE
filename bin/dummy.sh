#!/bin/bash

export __DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$( dirname ${__DIR} )/src/

python -u ${PYTHONPATH}/amber/dummy/dummy.py