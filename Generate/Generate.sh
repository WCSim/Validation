#!/bin/bash

WCSim $1 $ValidationPath/Generate/macReference/tune/tuning_parameters.mac
$ValidationPath/Generate/daq_readfilemain $2
