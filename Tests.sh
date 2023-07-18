#!/bin/bash

#build the comparison script
cd $ValidationPath
make

#checkout the validation webpage branch to a new location
cd $ValidationPath
if [ ! -d "${ValidationPath}/Webpage" ]; then
    git clone https://github.com/WCSim/Validation.git --single-branch --depth 1 -b gh-pages ./Webpage
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

if [ $1 -eq 1 ]
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
  <td rowspan='6'>"${TRAVIS_COMMIT}"</td>" >> $ValidationPath/Webpage/results.html.new;
    if [ ${TRAVIS_PULL_REQUEST} -ge 0 ]; then
	TRAVIS_PULL_REQUEST_LINK="<a href=https://github.com/WCSim/WCSim/pulls/"${TRAVIS_PULL_REQUEST}">"
    fi
    echo "  <td rowspan='6'>"${TRAVIS_PULL_REQUEST_LINK}${TRAVIS_COMMIT_MESSAGE}"</td>">> $ValidationPath/Webpage/results.html.new;


    ##### loop over the possible subjobs
    for isub in {0..5}; do
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
		    #note that there are 5 tests, but use an extra (first) column for the time to run WCSim
		    if [ "$isub" -ge 0 ] && [ "$isub" -le 5 ]; then
			subjobtag=${i}_sub${isub}
		    else
			continue
		    fi
		else
		    rowspan=" rowspan='6'"
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
    cp $ValidationPath/Webpage/results.html.new $ValidationPath/Webpage/results.html
    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}

i=0
   while read line
    do

        if [ "${line::1}" != "#" ]
        then
            i=$(expr 1 + $i)
	    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i
	    test=$(echo $line | cut -f2 -d' ')
	    echo placeholder > $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i/placeholder
	    if [ "$test" == "PhysicsValidation"  ]; then
		for isub in {0..5}; do
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

fi





#########################################################################################



################################### Running tests ######################################


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
	time=`more timetest |grep user |  cut -f2 -d' '`

	#check that the expected binary output is found
	if [ ! -e $var2 ]
	then
            pass=#FF0000
            ret=1
	else
            pass=#00FF00
            ret=0
	fi

	#update webpage with result
	cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
	head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$i:$pass: | sed s:${TRAVIS_COMMIT}"Text"$i:$time: | sed s:${TRAVIS_COMMIT}"Link"$i:${TRAVIS_COMMIT}/log${i}.txt: > $ValidationPath/Webpage/results.html.new

    fi
    #############################################################

    ################## File Test #######################

    if [ $test == "FileTest"  ]
    then

        if [ ! -e $var1 ]
        then
            pass=#FF0000
	    text="Not present"
	    ret=0
        else
            pass=#00FF00
	    text="Present"
	    ret=1
        fi

	file="index.html"

        cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
        head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$i:$pass: | sed s:${TRAVIS_COMMIT}"Text"$i:$text: | sed s:${TRAVIS_COMMIT}"Link"$i:$file: > $ValidationPath/Webpage/results.html.new
    fi
    #############################################################

    ################## Physics Validation #######################


    if [ $test == "PhysicsValidation" ]
    then

	#setup bash arrays to store the result of each subtest
	declare -a time
	declare -a pass
	declare -a link
	isubjob=0
	
	#first run WCSim with the chosen mac file
	/usr/bin/time -p --output=timetest $ValidationPath/$var1 $ValidationPath/Generate/macReference/$var2 ${var3}.root |& tee wcsim_run.out
	link[$isubjob]=""
	
	if [ $? -ne 0 ]; then
	    pass[$isubjob]=#FF0000
            time[$isubjob]="Failed to run WCSim"
            ret=1
	else
	    pass[$isubjob]=#00FF00
	    time[$isubjob]=`more timetest |grep user |  cut -f2 -d' '`

	    #then compare the output root files with the reference
	    # Note that there are up to 3 reference files, one for each WCSimRootEvent (PMT type)
	    wcsim_has_output=0
	    for pmttype in wcsimrootevent wcsimrootevent2 wcsimrootevent_OD; do
		#check if the file exists (and therefore whether the PMT type exists in the current geometry)
		rootfilename=${var3}_analysed_${pmttype}.root
		isubjob=$(expr $isubjob + 1)
		if [ -f "$rootfilename" ]; then
		    wcsim_has_output=1
		    $ValidationPath/Compare/compareroot $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/$isubjob/ $rootfilename $ValidationPath/Compare/Reference/$rootfilename
		    link[$isubjob]=${TRAVIS_COMMIT}/${i}/$isubjob/index.html
		    if [ $? -ne 0 ]; then
			pass[$isubjob]=#FF0000
			time[$isubjob]="Failed ${pmttype} plot comparisons"
			ret=1
		    else
			pass[$isubjob]=#00FF00
			time[$isubjob]="${pmttype} plot pass"
		    fi
		else
		    pass[$isubjob]=#000000
		    time[$isubjob]="No ${pmttype} in geometry"
		    link[$isubjob]=""
		fi
	    done

	    #then compare the output geofile.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    diff $ValidationPath/Compare/Reference/$var4 $var4 > $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/${var4}.diff.txt

	    if [ $? -ne 0 ]
	    then
		pass[$isubjob]=#FF0000
		time[$isubjob]="Failed geofile comparisons"
		link[$isubjob]=${TRAVIS_COMMIT}/${i}/${var4}.diff.txt
	    else
		pass[$isubjob]=#00FF00
		time[$isubjob]="Geofile diff pass"
		link[$isubjob]=""
	    fi

	    #then compare the output bad.txt with the reference
	    isubjob=$(expr $isubjob + 1)
	    badfilename=${var3}_bad.txt
	    if [ -f $badfilename ]; then
		rm -f $badfilename
	    fi
	    for greps in "GeomNav1002" "Optical photon is killed because of missing refractive index"; do
		grepcount=$( grep -c "\"$greps\"" wcsim_run.out )
		echo "\"$greps\"" $grepcount >> $badfilename
	    done
	    diff $ValidationPath/Compare/Reference/$badfilename $badfilename > $ValidationPath/Webpage/${TRAVIS_COMMIT}/${i}/${var3}_bad.diff.txt

	    if [ $? -ne 0 ]
	    then
		pass[$isubjob]=#FF0000
		time[$isubjob]=$"Difference in number of stuck tracks or similar"
		link[$isubjob]=${TRAVIS_COMMIT}/${i}/${var3}_bad.diff.txt
	    else
		pass[$isubjob]=#00FF00
		time[$isubjob]="Num stuck track diff pass"
		link[$isubjob]=""
	    fi
	    
	fi

	#make sure the Webpage is up to date
	cd $ValidationPath/Webpage
	git pull
	cd -

	#now update the Webpage with the result of this test
        cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
	for isub in {0..5}; do
            subjobtag=${i}_sub${isub}
	    echo ${TRAVIS_COMMIT}"Pass"$subjobtag
	    echo ${pass[isub]}
	    echo ${time[isub]}
	    echo ${link[isub]}
            head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$subjobtag:${pass[isub]}: | sed s:${TRAVIS_COMMIT}"Text"$subjobtag:"${time[isub]}": | sed s:${TRAVIS_COMMIT}"Link"$subjobtag:${link[isub]}: > $ValidationPath/Webpage/results.html.new
	done
    fi
    #############################################################






done < $ValidationPath/tests.txt



#############################################################

############################## update webpage ################

cd $ValidationPath/Webpage

#add a default user, otherwise git complains
git config user.name "WCSim CI"
git config user.email "wcsim@wcsim.wcsim"


#WARNING: clashes are possible here, if two jobs get to the bit between pull & push at the same time
git pull

head -100000000 header.html > index.html
mv results.html.new results.html
head -100000000 results.html >> index.html
head -100000000 footer.html >>index.html

rm results.html.old

git add --all
git commit -a -m'CI update'
#git push
#> /dev/null 2>/dev/null

git push https://tdealtry:${GitHubToken}@github.com/WCSim/Validation.git gh-pages
#> /dev/null 2>/dev/null


#git push "https://${TRAVIS_SECURE_TOKEN_NAME}@${GH_REPO}" gh-pages > /dev/null 2>&1

exit $ret
