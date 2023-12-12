#!/bin/bash

WCSim $1 $ValidationPath/Generate/macReference/tune/tuning_parameters.mac
for pmttype in 0 1 2; do
    $ValidationPath/Generate/daq_readfilemain $2 0 $pmttype
done
