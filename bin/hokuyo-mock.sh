#!/bin/bash

export __DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=${__DIR}/../src/

python -u ${__DIR}/../src/amber/hokuyo/hokuyo_mock.py