#! /bin/bash

#If you're in docker, run with:
# cd $WCSIMDIR
# ./MakeReference.sh
#
#If you're not in docker, setup WCSim and then run with:
# ./MakeReference.sh $PWD `which WCSim`

cd $WCSIMDIR
pwd
WCSIMVALIDATIONDIR=${1:-/root/Validation/}

#compile the plot-making macro
g++ $WCSIMVALIDATIONDIR/Generate/daq_readfilemain.C -g3 -o $WCSIMVALIDATIONDIR/Generate/daq_readfilemain `root-config --libs --cflags` -L $WCSIMDIR -lWCSimRoot -I $WCSIMDIR/include

#run WCSim
for mac in `ls $WCSIMVALIDATIONDIR/Generate/macReference/*.mac`
do
    echo $mac
    ${2:-./exe/bin/Linux-g++/WCSim} $mac
done

#generate plots
for file in `ls *.root`
do
    echo $file
    $WCSIMVALIDATIONDIR/Generate/daq_readfilemain $file
    sleep 5
done

#overwrite the reference plots
for output in `ls ./analysed_*.root`
do
    echo $output
    cp $output $WCSIMVALIDATIONDIR/Compare/Reference/
done