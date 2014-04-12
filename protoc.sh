#!/bin/bash

set -x

export ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export AMBER_DIR=${ROOT_DIR}/src/amber
export COMMON_DIR=${AMBER_DIR}/common

protoc -I ${COMMON_DIR} --python_out=${COMMON_DIR} ${COMMON_DIR}/drivermsg.proto
for pp in hokuyo roboclaw dummy; do
    protoc -I ${COMMON_DIR} -I ${AMBER_DIR}/${pp} --python_out=${AMBER_DIR}/${pp} ${AMBER_DIR}/${pp}/${pp}.proto
done
