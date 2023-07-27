#!/bin/bash

mkdir build install
cd build
if [ $1 -eq 1 ]; then
    extra_options="WCSim_Geometry_Overlaps_CHECK=ON"
fi
cmake -DWCSim_DEBUG_COMPILE_FLAG=ON $extra_options -DCMAKE_INSTALL_PREFIX=../install/ ../src/
make
make install
