#! /bin/bash

cd $WCSIMDIR
echo 'Creating reference WCSim output from '$PWD

#Run WCSim
for mac in `ls /opt/HyperK/Validation/Generate/macReference/*.mac`
do
    echo $mac
    ./exe/bin/Linux-g++/WCSim $mac
done

#Get the relevant histograms from WCSim
for file in `ls *.root`
do
    echo $file
    /opt/HyperK/Validation/Generate/daq_readfilemain $file
done

#Move the histogram files to the reference location
for output in `ls ./analysed_*.root`
do
    echo $output
    cp $output /opt/HyperK/Validation/Compare/Reference/
done
