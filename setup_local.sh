#!/bin/bash

source /t2k/hyperk/software/hyperk-releases/v1.3.5/hk-hyperk/Source_At_Start.sh; source /t2k/hyperk/software/wcsim-head/build/bin/this_wcsim.sh;
export ValidationPath=$PWD
if [ "$1" -eq 1 ]; then
echo "Building for first time so change some file paths..."
cd Generate/macReference/
sed -i 's!/opt/Validation/!!g' *.mac
cd -
fi
