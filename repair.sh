#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

find ${__dir} -name *pb2.py -exec sed -i 's/^import drivermsg_pb2/from amber.common import drivermsg_pb2/g' {} \;
