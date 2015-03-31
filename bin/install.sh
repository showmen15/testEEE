#!/bin/bash

export __dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export __dir="$( dirname ${__dir} )"

command -v virtualenv >/dev/null 2>&1 || { echo >&2 "I require \`virtualenv\` but it's not installed. Aborting."; exit 1; }

if [ ! -d ${__dir}/__envi ]
then
    if [ -x "$(command -v pypy)" ]
    then
        virtualenv -p pypy ${__dir}/__envi
    else
        virtualenv ${__dir}/__envi
    fi
fi

. ${__dir}/__envi/bin/activate

set -x

${__dir}/__envi/bin/pip install --upgrade distribute
${__dir}/__envi/bin/pip install --upgrade -r ${__dir}/requirements.txt

pushd ${__dir}
    ${__dir}/protoc.sh
popd