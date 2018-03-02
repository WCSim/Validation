#!/bin/bash

cd $ValidationPath/Compare
g++ compareroot.cpp -o compareroot `root-config --libs --cflags`
cd ../
git clone https://github.com/wcsimtravis/WCSim.git -b gh-pages ./Webpage
cd /root/HyperK/WCSim

echo showing travis commit
echo ${TRAVIS_COMMIT}

ret=0

##################### Setting up new table entry #############################

if [ $1 -eq 1 ]
then	    
    
    cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
    echo "
            <tr>
            <th scope='col'><div align='center'>Commit ID</div></th>
            <th scope='col'><div align='center'>Description</div></th>
" >$ValidationPath/Webpage/results.html.new;
    
    
    while read line
    do
	
	if [ ${line::1} != "#" ]
	then
	    
            name=$(echo $line | cut -f1 -d' ')
	    echo "  <th scope='col'><div align='center'>"$name"</div></th>" >> $ValidationPath/Webpage/results.html.new;
	    
	fi
	
    done < $ValidationPath/tests.txt
    
    echo " </tr> 
 <tr>
 <td>"${TRAVIS_COMMIT}"</td>
 <td>"${TRAVIS_COMMIT_MESSAGE}"</td>">> $ValidationPath/Webpage/results.html.new;
    
    
    i=0
    while read line
    do
	
        if [ ${line::1} != "#" ]
        then
	    i=$(expr 1 + $i)
            name=$(echo $line | cut -f1 -d' ')
            echo "  <td bgcolor=\""${TRAVIS_COMMIT}"Pass"$i"\"><a href='"${TRAVIS_COMMIT}"Link"$i"'>"${TRAVIS_COMMIT}"Text"$i$"</td>" >> $ValidationPath/Webpage/results.html.new;
	    
        fi
	
    done < $ValidationPath/tests.txt
    
    echo " </tr>
 " >> $ValidationPath/Webpage/results.html.new


    head -300 $ValidationPath/Webpage/results.html.old >>$ValidationPath/Webpage/results.html.new
    cp $ValidationPath/Webpage/results.html.new $ValidationPath/Webpage/results.html
    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}

i=0
   while read line
    do

        if [ ${line::1} != "#" ]
        then
            i=$(expr 1 + $i)
	    mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i
	    echo placeholder > $ValidationPath/Webpage/${TRAVIS_COMMIT}/$i/placeholder
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
    
    if [ ${line::1} != "#" ]
    then
	
        name=$(echo $line | cut -f1 -d' ')
        test=$(echo $line | cut -f2 -d' ')
        var1=$(echo $line | cut -f3 -d' ')
        var2=$(echo $line | cut -f4 -d' ')
        var3=$(echo $line | cut -f5 -d' ')
        var4=$(echo $line | cut -f6 -d' ')
	
	i=$(expr $i + 1)
	
	if [ $i -eq $1 ]
	then
	    
################## Build Test #######################
	    
            if [ $test == "BuildTest"  ]
            then
		
		/usr/bin/time -p --output=timetest $var1 > $ValidationPath/Webpage/${TRAVIS_COMMIT}/"log"$1
		ret=${?} 
		time=`more timetest |grep sys |  cut -f2 -d' '`
		
		if [ ! -e $var2 ]
		then
                    pass=#FF0000
		    
		else
                    pass=#00FF00
		fi
		
		
		cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
		head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$1:$pass: | sed s:${TRAVIS_COMMIT}"Text"$i:$time: | sed s:${TRAVIS_COMMIT}"Link"$1:${TRAVIS_COMMIT}/log$1: > $ValidationPath/Webpage/results.html.new
		
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
                head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$1:$pass: | sed s:${TRAVIS_COMMIT}"Text"$i:$text: | sed s:${TRAVIS_COMMIT}"Link"$1:$file: > $ValidationPath/Webpage/results.html.new
	    fi
#############################################################
		
################## Physics Validation #######################
	    
	    
	    if [ $test == "PhysicsValidation" ]
            then
		
		/usr/bin/time -p --output=timetest $var1 $var2

		if [ $? -ne 0 ]
                then
		    pass=#FF0000
                    time="Failed"
                    ret=1
		else
		    time=`more timetest |grep sys |  cut -f2 -d' '`
		    
		    $ValidationPath/Compare/compareroot $ValidationPath/Webpage/${TRAVIS_COMMIT}/$1 "analysed_"$name".root" $var3
		    
		    
		    if [ $? -ne 0 ]
		    then
			pass=#FF0000
			time="Failed"
			ret=1
		    else
			pass=#00FF00
			ret=0
		    fi
		fi

		cd $ValidationPath/Webpage
		git pull
		cd -
		
                cp $ValidationPath/Webpage/results.html $ValidationPath/Webpage/results.html.old
                head -1000000 $ValidationPath/Webpage/results.html.old | sed s:${TRAVIS_COMMIT}"Pass"$1:$pass: | sed s:${TRAVIS_COMMIT}"Text"$i:$time: | sed s:${TRAVIS_COMMIT}"Link"$1:${TRAVIS_COMMIT}/$1/index.html: > $ValidationPath/Webpage/results.html.new
		
	    fi
#############################################################		
	    
	    
	    
	fi
	
    fi
    
    
done < $ValidationPath/tests.txt



#############################################################

############################## update webpage ################

cd $ValidationPath/Webpage

git pull

head -100000000 header.html > index.html
mv results.html.new results.html
head -100000000 results.html >> index.html
head -100000000 footer.html >>index.html

rm results.html.old

git add --all
git commit -a -m'Travis update'
#git push
#> /dev/null 2>/dev/null

git push https://brichards64:$GitHubToken@github.com/wcsimtravis/WCSim  
#> /dev/null 2>/dev/null


#git push "https://${TRAVIS_SECURE_TOKEN_NAME}@${GH_REPO}" gh-pages > /dev/null 2>&1

exit $ret