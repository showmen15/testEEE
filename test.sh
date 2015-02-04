#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd ${__dir}
    ${__dir}/clean.sh
    ${__dir}/protoc.sh
    PYTHONPATH=src python setup.py test
    ${__dir}/clean.sh
popd