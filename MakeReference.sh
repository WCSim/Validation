#! /bin/bash

for mac in `ls /root/Validation/Generate/macReference/*.mac`
do
echo $mac
./exe/bin/Linux-g++/WCSim $mac
done

for file in `ls *.root`
do
echo $file
/root/Validation/Generate/daq_readfilemain $file
done

for output in `ls ./analysed_*.root`
do
echo $output
cp $output /root/Validation/Compare/Reference/
done