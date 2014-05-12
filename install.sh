#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -d ${__dir}/__envi ]
then
    virtualenv ${__dir}/__envi
fi

. ${__dir}/__envi/bin/activate
${__dir}/__envi/bin/python ${__dir}/setup.py install