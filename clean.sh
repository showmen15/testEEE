#!/bin/bash

set -x
rm -rf *.egg-info/ build/ dist/
find . -name *.pyc -exec rm {} \;
