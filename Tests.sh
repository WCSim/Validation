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

##################### Setting up new table entry #############################

if [ $1 -eq 0 ]
then
    if [ $TRAVIS_PULL_REQUEST != "false" ]
    then
	TRAVIS_COMMIT_MESSAGE=" Pull Request #${TRAVIS_PULL_REQUEST}"
    fi

    cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old

    ##### write the header row
    echo "
 <tr>
  <th scope='col'><div align='center'>Commit ID</div></th>
  <th scope='col'><div align='center'>Description</div></th>
" >$ValidationPath/Webpage/results.html.new;


    while read line
    do
	if [ "${line::1}" != "#" ]; then
            name=$(echo $line | cut -f1 -d' ')
	    test=$(echo $line | cut -f2 -d' ')
	    echo "  <th scope='col'><div align='center'>"$name"</div></th>" >> $ValidationPath/Webpage/results.html.new;
	fi
    done < $ValidationPath/tests.txt

    echo " </tr>" >> $ValidationPath/Webpage/results.html.new;

    ##### write the contents row
    echo " <tr>
  <td rowspan='7'>"${TRAVIS_COMMIT}"</td>" >> $ValidationPath/Webpage/results.html.new;
    if [ ${TRAVIS_PULL_REQUEST} -ge 0 ]; then
	TRAVIS_PULL_REQUEST_LINK="<a href=https://github.com/WCSim/WCSim/pull/"${TRAVIS_PULL_REQUEST}">"
    fi
    echo "  <td rowspan='7'>"${TRAVIS_PULL_REQUEST_LINK}${TRAVIS_COMMIT_MESSAGE}"</td>">> $ValidationPath/Webpage/results.html.new;


    ##### loop over the possible subjobs
    for isub in {0..6}; do
	if [ "$isub" -ge 1 ]; then
	    echo " <tr>" >> $ValidationPath/Webpage/results.html.new;
	fi
	##### loop over tests.txt jobs list
	i=0
	while read line
	do
            if [ "${line::1}" != "#" ]; then
		i=$(expr 1 + $i)
		name=$(echo $line | cut -f1 -d' ')
		test=$(echo $line | cut -f2 -d' ')
		if [ "$test" == "PhysicsValidation"  ]; then
		    rowspan=""
		    #note that there are 6 tests, but use an extra (first) column for the time to run WCSim
		    if [ "$isub" -ge 0 ] && [ "$isub" -le 6 ]; then
			subjobtag=${i}_sub${isub}
		    else
			continue
		    fi
		else
		    rowspan=" rowspan='7'"
		    if [ "$isub" -ge 1 ]; then
			continue;
		    else
			subjobtag=${i}
		    fi
		fi
		echo "  <td bgcolor=\""${TRAVIS_COMMIT}"Pass"${subjobtag}${rowspan}"\"><a href='"${TRAVIS_COMMIT}"Link"$subjobtag"'>"${TRAVIS_COMMIT}"Text"$subjobtag$"</td>" >> $ValidationPath/Webpage/results.html.new;
	    fi
	done < $ValidationPath/tests.txt
	echo " </tr>" >> $ValidationPath/Webpage/results.html.new
    done


    head -300 $ValidationPath/Webpage/results.html.old >>$ValidationPath/Webpage/results.html.new
    rm $ValidationPath/Webpage/results.html.old
    mv $ValidationPath/Webpage/results.html.new $ValidationPath/Webpage/results.html
    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}

    i=0
    while read line; do
        if [ "${line::1}" != "#" ]
        then
            i=$(expr 1 + $i)
	    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i
	    test=$(echo $line | cut -f2 -d' ')
	    echo placeholder > $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i/placeholder
	    if [ "$test" == "PhysicsValidation"  ]; then
		for isub in {0..6}; do
		    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i/$isub
		    echo placeholder > $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i/$isub/placeholder
		done
	    fi
        fi
    done < $ValidationPath/tests.txt


    echo ${TRAVIS_COMMIT} >$ValidationPath/Webpage/folderlist.new
    head -35 $ValidationPath/Webpage/folderlist >> $ValidationPath/Webpage/folderlist.new
    mv $ValidationPath/Webpage/folderlist.new $ValidationPath/Webpage/folderlist

##### clean up ####
    folder=0
    while read line
    do

        folder=$(expr 1 + $folder)

        if [ $folder -ge 30 ]
        then
            rm -rf $line
        fi

    done <  $ValidationPath/Webpage/folderlist

##################

    #push this new table entry now, before anything is filled
    # Note that there should be no git clashes, because
    #  - job 1 always happens first, and before all other jobs
    #  - starting job 1 always stops other jobs from previous CI runs

    cd $ValidationPath/Webpage
    
    #setup the commit
    echo "Adding"
    git add --all
    git commit -a -m'CI update'

    #attempt to push
    git push https://tdealtry:${GitHubToken}@github.com/WCSim/Validation.git gh-pages

    cd -
fi





#########################################################################################



################################### Running tests ######################################

#setup bash arrays to store the result of each (sub)test
declare -a repl
declare -a time
declare -a pass
declare -a link
ichange=0

i=0

while read line
do

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

################## Build Test #######################

    if [ $test == "BuildTest"  ]
    then
	#build
	# the build log is stored to be accessible in the webpage
	/usr/bin/time -p --output=timetest $var1 |& tee $ValidationPath/Webpage/${TRAVIS_COMMIT}/"log"${i}.txt
	ret=${?}
	time[ichange]=`more timetest |grep user |  cut -f2 -d' '`

	#check that the expected binary output is found
	if [ ! -e $var2 ]
	then
            pass[ichange]=#FF0000
            ret=1
	else
            pass[ichange]=#00FF00
            ret=0
	fi
	link[ichange]=0
	repl[ichange]=$i
	ichange=$(expr $ichange + 1)
    fi
    #############################################################

    ################## File Test #######################

    if [ $test == "FileTest"  ]
    then

        if [ ! -e $var1 ]
        then
            pass[ichange]=#FF0000
	    time[ichange]="Not present"
	    ret=0
        else
            pass[ichange]=#00FF00
	    time[ichange]="Present"
	    ret=1
        fi
	link[ichange]=0
	repl[ichange]=$i
	ichange=$(expr $ichange + 1)

	file="index.html"
    fi
    #############################################################

    ################## Physics Validation #######################


    if [ $test == "PhysicsValidation" ]
    then

	isubjob=0

	#first run WCSim with the chosen mac file
	/usr/bin/time -p --output=timetest $ValidationPath/$var1 $ValidationPath/Generate/macReference/$var2 ${var3}.root |& tee wcsim_run.out
	link[$ichange]=""
	repl[ichange]=${i}_sub${isubjob}

	if [ $? -ne 0 ]; then
	    pass[$ichange]=#FF0000
            time[$ichange]="Failed to run WCSim"
            ret=1
	else
	    pass[$ichange]=#00FF00
	    time[$ichange]=`more timetest |grep user |  cut -f2 -d' '`" sec"

	    #then compare the output root files with the reference
	    # Note that there are up to 3 reference files, one for each WCSimRootEvent (PMT type)
	    wcsim_has_output=0
	    for pmttype in wcsimrootevent wcsimrootevent2 wcsimrootevent_OD; do
		#check if the file exists (and therefore whether the PMT type exists in the current geometry)
		rootfilename=${var3}_analysed_${pmttype}.root
		isubjob=$(expr $isubjob + 1)
		ichange=$(expr $ichange + 1)
		repl[ichange]=${i}_sub${isubjob}
		if [ -f "$rootfilename" ]; then
		    wcsim_has_output=1
		    link[$ichange]=${TRAVIS_COMMIT}/${i}/$isubjob/index.html
		    $ValidationPath/Compare/compareroot $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/$isubjob/ $rootfilename $ValidationPath/Compare/Reference/$rootfilename
		    if [ $? -ne 0 ]; then
			pass[$ichange]=#FF0000
			time[$ichange]="Failed ${pmttype} plot comparisons"
			ret=1
		    else
			pass[$ichange]=#00FF00
			time[$ichange]="${pmttype} plot pass"
		    fi
		else
		    pass[$ichange]=#000000
		    time[$ichange]="No ${pmttype} in geometry"
		    link[$ichange]=""
		fi
	    done
	    if [ $wcsim_has_output -eq 0 ]; then
		ret=1
	    fi

	    #then compare the output geofile.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    ichange=$(expr $ichange + 1)
	    repl[ichange]=${i}_sub${isubjob}
	    geomdifffilename=${var4}.diff.txt
	    diff $ValidationPath/Compare/Reference/$var4 $var4 > $geomdifffilename

	    if [ -s $geomdifffilename ]
	    then
		pass[$ichange]=#FF0000
		time[$ichange]="Failed geofile comparisons"
		link[$ichange]=${TRAVIS_COMMIT}/${i}/${var4}.diff.txt
		mv $geomdifffilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    else
		pass[$ichange]=#00FF00
		time[$ichange]="Geofile diff pass"
		link[$ichange]=""
	    fi

	    #then compare the output bad.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    ichange=$(expr $ichange + 1)
	    repl[ichange]=${i}_sub${isubjob}
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

	    if [ -s $baddifffilename ]
	    then
		pass[$ichange]=#FF0000
		time[$ichange]="Difference in number of stuck tracks or similar"
		link[$ichange]=${TRAVIS_COMMIT}/${i}/${var3}_bad.diff.txt
		mv $baddifffilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    else
		pass[$ichange]=#00FF00
		time[$ichange]="Num stuck track diff pass"
		link[$ichange]=""
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
		pass[$ichange]=#FF0000
		time[$ichange]="Geoemtry warnings exists"
		link[$ichange]=${TRAVIS_COMMIT}/${i}/$impossiblefilename
		mv $impossiblefilename $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/
		ret=1
	    else
		pass[$ichange]=#00FF00
		time[$ichange]="Geometry warnings pass"
		link[$ichange]=""
	    fi

	    #and final increment of $ichange for the next time round the loop
	    ichange=$(expr $ichange + 1)
	fi

    fi
    #############################################################






done < $ValidationPath/tests.txt



#############################################################

############################## update webpage ################

cd $ValidationPath/Webpage

#setup a loop here, to prevent clashes when multiple jobs change the webpage at the same time
# make it a for loop, so there isn't an infinite loop
#  100 attempts, 15 seconds between = 25 minutes of trying
for iattempt in {0..100}; do
    #reset the main webpage files
    git checkout *.html

    #get the latest version of the webpage
    git pull --no-rebase

    #apply the changes to it
    nchanges=${#pass[@]}
    nchanges_to_loop=$(expr $nchanges - 1)
    for ichange in $( seq 0 ${nchanges_to_loop} ); do
	echo
	echo Saving results with the following at ${repl[ichange]}:
	echo ${pass[ichange]}
	echo ${time[ichange]}
	echo ${link[ichange]}
        head -1000000 results.html | sed s:${TRAVIS_COMMIT}"Pass"${repl[ichange]}:"${pass[ichange]}": | sed s:${TRAVIS_COMMIT}"Text"${repl[ichange]}:"${time[ichange]}": | sed s:${TRAVIS_COMMIT}"Link"${repl[ichange]}:"${link[ichange]}": > results.html.new	
	#copy the new results to the standard results, so that the updated version is available next time through the ichange loop
	mv results.html.new results.html
    done

    #build the new webpage from components
    head -100000000 header.html > index.html
    head -100000000 results.html >> index.html
    head -100000000 footer.html >>index.html

    #setup the commit
    git add --all
    git commit -a -m'CI update. Job: '$1

    #attempt to push
    git push https://tdealtry:${GitHubToken}@github.com/WCSim/Validation.git gh-pages
    if [ "$?" -eq 0 ]; then
	break
    fi

    #if it didn't work, undo the last commit
    git reset HEAD~1

    #have a rest before trying again
    sleep 15
done

exit $ret
