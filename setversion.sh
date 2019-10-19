#!/bin/sh

set -xe
TAG=$(git describe --abbrev=0 --tags)

sed -i "s/PYPIVERSION/${TAG}/g" setup.py