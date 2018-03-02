#!/bin/bash

WCSim=$HYPERKDIR/WCSim
export LD_LIBRARY_PATH=$WCSim:$LD_LIBRARY_PATH

g++ $ValidationPath/Generate/daq_readfilemain.C -o $ValidationPath/Generate/daq_readfilemain `root-config --libs --cflags` -L $WCSim -lWCSimRoot -I $WCSim/include

$WCSim/exe/bin/Linux-g++/WCSim $1
$ValidationPath/Generate/daq_readfilemain *.root
