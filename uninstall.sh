#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

rm -rf ${__dir}/__envi
find ${__dir} -name *.pyc -exec rm -rf {} \;