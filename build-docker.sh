#!/usr/bin/env bash

if [ -z "$RELEASE_VERSION" ]; then
    echo "Error: RELEASE_VERSION must be set."
    exit 1
fi

make
mkdir build && cd build
../packaging/package-all.sh ${RELEASE_VERSION} $(pwd)
cd ..

