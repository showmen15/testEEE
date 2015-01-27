#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export __dir="$( dirname ${__dir} )"

if [ -d ${__dir}/__envi ]
then
    . ${__dir}/__envi/bin/activate
    export PYTHONPATH=${__dir}/src

    if [ -z "${_APP_PROFILE}" ];
    then
        ${__dir}/__envi/bin/python -u ${PYTHONPATH}/amberdriver/collision_avoidance/collision_avoidance.py
    else
        export _APP_TEMP=$(mktemp -d)

        ${__dir}/__envi/bin/python -u -m cProfile -o ${_APP_TEMP}/output.pstats ${PYTHONPATH}/amberdriver/collision_avoidance/collision_avoidance_controller.py

        ${__dir}/__envi/bin/gprof2dot -f pstats --output ${_APP_TEMP}/output.dot ${_APP_TEMP}/output.pstats
        # TODO(paoolo) check if `dot` exists?
        /usr/bin/dot -Tpng ${_APP_TEMP}/output.dot -o ${__dir}/profile-collision_avoidance-$(date +"%Y%m%d-%H%M%S").png

        rm -rf ${_APP_TEMP}
    fi
fi