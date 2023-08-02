#!/bin/bash

#checkout the validation webpage branch to a new location
cd $ValidationPath
if [ ! -d "${ValidationPath}/Webpage" ]; then
    git clone https://github.com/WCSim/Validation.git --single-branch --depth 1 -b gh-pages ./Webpage
    cd Webpage
    #add a default user, otherwise git complains
    git config user.name "WCSim CI"
    git config user.email "wcsim@wcsim.wcsim"
    cd -
fi

if [[ -z ${TRAVIS_PULL_REQUEST} ]]; then
    TRAVIS_PULL_REQUEST=false
fi

echo showing travis commit
echo ${TRAVIS_COMMIT}
echo showing travis pull request
echo ${TRAVIS_PULL_REQUEST}


#we are only updating the colours of the table of jobs for a single CI run
RUNDIR=$ValidationPath/Webpage/$TRAVIS_COMMIT/
RUNWEBPAGE=$RUNDIR/index.html

#loop over subjob directories
for jobnum in {0..100}; do
    if [ ! -d $RUNDIR/$jobnum ]; then
	break
    fi
    colour=`tail -1 $RUNDIR/$jobnum/index.html`
    echo colour
    #now update the colour of the job
    cat $RUNWEBPAGE | sed s:"COLOUR"${jobnum}:$colour: > $RUNWEBPAGE.new
    mv $RUNWEBPAGE.new $RUNWEBPAGE
fi


#############################################################

############################## update webpage ################

#push this new table entry now
# There should be no clashes, as this is only run once, and after SetupWebpages.sh has produces the file

cd $ValidationPath/Webpage

#setup the commit
echo "Adding"
git add --all
git commit -a -m'CI update'

#attempt to push
git push https://tdealtry:${GitHubToken}@github.com/WCSim/Validation.git gh-pages
