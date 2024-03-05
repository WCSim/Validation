#!/bin/bash

#build the comparison script
cd $ValidationPath
make

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

#return to the WCSim directory
cd /opt/WCSim/install

if [[ -z ${TRAVIS_PULL_REQUEST} ]]; then
    TRAVIS_PULL_REQUEST=false
fi

echo showing travis commit
echo ${TRAVIS_COMMIT}
echo showing travis pull request
echo ${TRAVIS_PULL_REQUEST}

ret=0

################################### Running tests ######################################
# Each test has it's own webpage, so lets just build it as we go
TESTDIR=$ValidationPath/Webpage/$TRAVIS_COMMIT/$1
TESTWEBPAGE=$TESTDIR/index.html

#first make the directory
mkdir $TESTDIR

#start with the header
cat $ValidationPath/Webpage/templates/test/header.html > $TESTWEBPAGE

# add the details of the job
if [ $TRAVIS_PULL_REQUEST != "false" ]; then
    TRAVIS_COMMIT_MESSAGE=" Pull Request #${TRAVIS_PULL_REQUEST}: ${TRAVIS_PULL_REQUEST_TITLE}"
fi
echo "
<h2>"${TRAVIS_COMMIT}"</h2>
<h3>"${TRAVIS_PULL_REQUEST_LINK}${TRAVIS_COMMIT_MESSAGE}"</h3>
" >> $TESTWEBPAGE

#loop over tests.txt to find the correct job we want to run (given by $1)
while read line; do
    #skip comments
    if [ "${line::1}" == "#" ]; then continue; fi

    name=$(echo $line | cut -f1 -d' ')
    test=$(echo $line | cut -f2 -d' ')
    var1=$(echo $line | cut -f3 -d' ')
    var2=$(echo $line | cut -f4 -d' ')
    var3=$(echo $line | cut -f5 -d' ')
    var4=$(echo $line | cut -f6 -d' ')
    var5=$(echo $line | cut -f7 -d' ')

    i=$(expr $i + 1)
    if [ "$i" -ne "$1" ]; then continue; fi

    echo Running test $i with name: $name of type: $test with variables: $var1 $var2 $var3 $var4 $var5

    # add the details of the test
    echo "
<h3>"$name"</h3>
" >> $TESTWEBPAGE
    
    ################## Physics Validation #######################
    if [ $test == "PhysicsValidation" ]; then

	#setup the table of tests
	echo "
<p>
<table  border='1' align='center'>
 <tr>
  <th scope='col'><div align='center'>Tests</div></th>
 </tr>
" >> $TESTWEBPAGE

	#define a function for adding a line
	# $1: cell colour
	# $2: link
	# $3: text
	add_entry() {
	    echo "
  <tr>
    <td bgcolor="$1">"$2" "$3"</td>
  </tr>
" >> $TESTWEBPAGE
	} #add entry

	#sanity check - ensure the reference file exists
	# This will purposefully fail jobs when new reference mac files are added, until the reference .root files are uploaded
    # Note that this only checks for the first ID PMT type (i.e. `wcsimrootevent` branch of the tree)
    #  This should be fine, but will break down if somehow `_2` or `_OD` are the only ones that exist in a future geometry
	rootfilename=${var3}_analysed_wcsimrootevent.root
	if [ ! -f $ValidationPath/Compare/Reference/$rootfilename ]; then
		add_entry "#FF00FF" "" "Reference file does not exist"
		ret=1
		continue
	fi

	#first run WCSim with the chosen mac file
	isubjob=0
	/usr/bin/time -p --output=timetest $ValidationPath/$var1 $ValidationPath/Generate/macReference/$var2 ${var3}.root |& tee wcsim_run.out

	if [ $? -ne 0 ]; then
	    add_entry "#FF0000" "" "Failed to run WCSim"
            ret=1
	else
	    time=`more timetest |grep user |  cut -f2 -d' '`" sec"
	    add_entry "#00FF00" "" "$time"

	    #then compare the output root files with the reference
	    # Note that there are up to 3 reference files, one for each WCSimRootEvent (PMT type)
	    wcsim_has_output=0
	    for pmttype in wcsimrootevent wcsimrootevent2 wcsimrootevent_OD; do
		isubjob=$(expr $isubjob + 1)
		#check if the file exists (and therefore whether the PMT type exists in the current geometry)
		rootfilename=${var3}_analysed_${pmttype}.root
		if [ -f "$rootfilename" ]; then
		    wcsim_has_output=1
		    link="<a href='${isubjob}/index.html'>"
		    mkdir $TESTDIR/${isubjob}
		    $ValidationPath/Compare/compareroot $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/$isubjob/ $rootfilename $ValidationPath/Compare/Reference/$rootfilename
		    if [ $? -ne 0 ]; then
			add_entry "#FF0000" "$link" "Failed ${pmttype} plot comparisons"
			ret=1
		    else
			add_entry "#00FF00" "$link" "${pmttype} plot pass"
		    fi
		else
		    add_entry "#000000" "" "No ${pmttype} in geometry"
		fi
	    done
	    if [ $wcsim_has_output -eq 0 ]; then
		ret=1
	    fi

	    #then compare the output geofile.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    geomdifffilename=${var4}.diff.txt
	    diff $ValidationPath/Compare/Reference/$var4 $var4 > $geomdifffilename

	    if [ -s $geomdifffilename ]
	    then
		add_entry "#FF0000" "<a href='${var4}.diff.txt'>" "Failed geofile comparisons"
		echo "Failed geofile comparisons:"
		cat $geomdifffilename
		mv $geomdifffilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    elif [ ! -f $ValidationPath/Compare/Reference/$var4 ]; then
		add_entry "#FF00FF" "" "Reference geofile not found"
	    else
		add_entry "#00FF00" "" "Geofile diff pass"
	    fi

	    #then compare the output bad.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    badfilename=${var3}_bad.txt
	    baddifffilename=${var3}_bad.diff.txt
	    if [ -f $badfilename ]; then
		rm -f $badfilename
	    fi
	    for greps in "GeomNav1002" "Optical photon is killed because of missing refractive index"; do
		grepcount=$( grep -c "$greps" wcsim_run.out )
		echo "\"$greps\"" $grepcount >> $badfilename
	    done
	    diff $ValidationPath/Compare/Reference/$badfilename $badfilename > $baddifffilename

	    if [ -s $baddifffilename ]; then
		add_entry "#FF0000" "<a href='${var3}_bad.diff.txt'>" "Difference in number of stuck tracks or similar"
		echo "Difference in number of stuck tracks or similar:"
		cat $baddifffilename
		mv $baddifffilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    elif [ ! -f $ValidationPath/Compare/Reference/$badfilename ]; then
		add_entry "#FF00FF" "" "Reference stuck tracks file not found"
	    else
		add_entry "#00FF00" "" "Num stuck track diff pass"
	    fi

	    #then just produce a grep of the impossible geometry warnings
	    isubjob=$(expr $isubjob + 1)
	    ichange=$(expr $ichange + 1)
	    repl[ichange]=${i}_sub${isubjob}
	    impossiblefilename=${var3}_impossible.txt
	    if [ -f $impossiblefilename ]; then
		rm -f $impossiblefilename
	    fi
	    for greps in "IMPOSSIBLE GEOMETRY" "*** G4Exception : GeomVol1002"; do
		grep "$greps" wcsim_run.out >> $impossiblefilename
	    done
	    if [ -s $impossiblefilename ]; then
		add_entry "#FF0000" "<a href='$impossiblefilename'>" "Geometry warnings exist"
		echo "Geometry warnings exist:"
		cat $impossiblefilename
		mv $impossiblefilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    else
		add_entry "#00FF00" "" "Geometry warnings pass"
	    fi

	fi #if WCSim running reported success

    fi #if not comment line
    #############################################################


done < $ValidationPath/tests.txt

#and add a footer to finish the webpage
cat $ValidationPath/Webpage/templates/test/footer.html >> $TESTWEBPAGE

#and a colour code at the bottom, that we can pull for the list of jobs page
if [ $ret -eq 0 ]; then
    echo "#00FF00" >> $TESTWEBPAGE
else
    echo "#FF0000" >> $TESTWEBPAGE
fi

#############################################################

############################## update webpage ################

cd $ValidationPath/Webpage

##push this new subjob result now
# There should be no clashes, as all we've done is updated this jobs' webpages

cd $ValidationPath/Webpage

#setup the commit
echo "Adding"
git add --all
git commit -a -m "CI update: add pages for test $1 for ${TRAVIS_COMMIT}"

#setup a loop here, to prevent clashes when multiple jobs change the webpage at the same time
# make it a for loop, so there isn't an infinite loop
#  100 attempts, 15 seconds between = 25 minutes of trying
#
#The CI is setup such that files will be touched by one job at once
# so it's just a matter of keeping pulling until we happen to be at the front of the queue
for iattempt in {0..100}; do
    #get the latest version of the webpage
    git pull --rebase

    #attempt to push
    git push https://tdealtry:${GitHubToken}@github.com/WCSim/Validation.git gh-pages
    if [ "$?" -eq 0 ]; then
	break
    fi

    #have a rest before trying again
    sleep 15
done

exit $ret
