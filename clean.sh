#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

set -x
rm -rf ${__dir}/*.egg-info/ ${__dir}/build/ ${__dir}/dist/ ${__dir}/*.egg
find ${__dir} -name *.pyc -exec rm {} \;
find ${__dir}/src -name *_pb2.py -exec rm {} \;
