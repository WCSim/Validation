#!/bin/bash

mkdir build install
cd build
cmake -DWCSim_DEBUG_COMPILE_FLAG=ON -DCMAKE_INSTALL_PREFIX=../install/ ../src/
make
make install
