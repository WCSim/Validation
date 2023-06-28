#! /bin/bash

cd $WCSIM_BUILD_DIR
echo Creating reference WCSim output from:
#Save the WCSim sha
cd ../src
git rev-list HEAD -1 > /opt/Validation/Compare/Reference/WCSimSHA
cd -

#Run WCSim
for mac in `ls /opt/Validation/Generate/macReference/*.mac`
do
    if [[ $mac == tuning_parameters.mac ]]; then
	continue
    fi
    echo $mac
    WCSim $mac /opt/Validation/Generate/macReference/tuning_parameters.mac
done

#Get the relevant histograms from WCSim
for file in `ls *.root`
do
    if [[ $file == analysed_* ]]; then
	continue
    elif [[ $file == *_flat.root ]]; then
	continue
    elif [[ $file == cosmicflux.root ]]; then
	continue
    fi
    echo $file
    /opt/Validation/Generate/daq_readfilemain $file
done

#Move the histogram files to the reference location
for output in `ls ./analysed_*.root`
do
    echo $output
    cp $output /opt/Validation/Compare/Reference/
done
