#!/bin/bash

set -x

export ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export AMBER_DIR=${ROOT_DIR}/src/amberdriver
export COMMON_DIR=${AMBER_DIR}/common

protoc -I ${COMMON_DIR} --python_out=${COMMON_DIR} ${COMMON_DIR}/drivermsg.proto
for pp in collision_avoidance dummy drive_to_point hokuyo roboclaw; do
    protoc -I ${COMMON_DIR} -I ${AMBER_DIR}/${pp} --python_out=${AMBER_DIR}/${pp} ${AMBER_DIR}/${pp}/${pp}.proto
done
protoc -I ${COMMON_DIR} -I ${AMBER_DIR}/collision_avoidance --python_out=${AMBER_DIR}/collision_avoidance ${AMBER_DIR}/collision_avoidance/roboclaw.proto

find ${ROOT_DIR} -name *pb2.py -exec sed -i 's/^import drivermsg_pb2/from amberdriver.common import drivermsg_pb2/g' {} \;
