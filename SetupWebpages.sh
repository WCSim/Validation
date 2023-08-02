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

##################### Setting up new table entry #############################
if [ $TRAVIS_PULL_REQUEST != "false" ]
then
    TRAVIS_COMMIT_MESSAGE=" Pull Request #${TRAVIS_PULL_REQUEST}"
fi

##### First update the list of commits
echo ${TRAVIS_COMMIT} > $ValidationPath/Webpage/folderlist.new
cat $ValidationPath/Webpage/folderlist >> $ValidationPath/Webpage/folderlist.new
mv $ValidationPath/Webpage/folderlist.new $ValidationPath/Webpage/folderlist


#### Update the main page
if [ ${TRAVIS_PULL_REQUEST} -ge 0 ]; then
    TRAVIS_PULL_REQUEST_LINK="<a href=https://github.com/WCSim/WCSim/pull/"${TRAVIS_PULL_REQUEST}">"
fi

#put all on one line, for easy removal
echo "
  <tr> <td><a href='"${TRAVIS_COMMIT}"/index.html'> "${TRAVIS_COMMIT}"</td> <td>"${TRAVIS_PULL_REQUEST_LINK}${TRAVIS_COMMIT_MESSAGE}"</td> </tr>
"> $ValidationPath/Webpage/body.html.new;

#update the body
head -300 $ValidationPath/Webpage/body.html >> $ValidationPath/Webpage/body.html.new
mv $ValidationPath/Webpage/body.html.new $ValidationPath/Webpage/body.html

#build the webpage
cat $ValidationPath/Webpage/templates/main/header.html > $ValidationPath/Webpage/index.html
cat $ValidationPath/Webpage/body.html >> $ValidationPath/Webpage/index.html
cat $ValidationPath/Webpage/templates/main/footer.html >> $ValidationPath/Webpage/index.html


#### Make the test webpage
#make the new directory
mkdir $ValidationPath/Webpage/${TRAVIS_COMMIT}

#first the details of the job
echo "
<h2>"${TRAVIS_COMMIT}"</h2>
<h3>"${TRAVIS_PULL_REQUEST_LINK}${TRAVIS_COMMIT_MESSAGE}"</h3>
" > $ValidationPath/Webpage/${TRAVIS_COMMIT}/body.html

#then the table of tests
echo "
<p>
<table  border='1' align='center'>
 <tr>
  <th scope='col'><div align='center'>Physics test</div></th>
 </tr>
" >> $ValidationPath/Webpage/${TRAVIS_COMMIT}/body.html

#then the list of tests
# loop over tests.txt jobs list
itest=0
while read line; do
    if [ "${line::1}" != "#" ]; then
	itest=$(expr 1 + $itest)
	name=$(echo $line | cut -f1 -d' ')
	#this way we set the default colour (cyan)
	# and have an unused tag that we can use sed with to fill in the result colour later
	printf -v itestpad "%04d" $itest
	echo "
  <tr>
    <td bgcolor='#00FFFF'COLOUR"${itestpad}"><a href='"$itest"/index.html'>"${name}"</td>
  </tr>
" >> $ValidationPath/Webpage/${TRAVIS_COMMIT}/body.html
    fi
done < $ValidationPath/tests.txt

#build the webpage
cat $ValidationPath/Webpage/templates/run/header.html > $ValidationPath/Webpage/${TRAVIS_COMMIT}/index.html
cat $ValidationPath/Webpage/${TRAVIS_COMMIT}/body.html >> $ValidationPath/Webpage/${TRAVIS_COMMIT}/index.html
cat $ValidationPath/Webpage/templates/run/footer.html >> $ValidationPath/Webpage/${TRAVIS_COMMIT}/index.html


#############################################################

############################## update webpage ################

#push this new table entry now
# There should be no clashes, since only one CI job that calls this script
#  runs at once due to concurrency settings

cd $ValidationPath/Webpage

##### clean up old folders ####
# save 35 results. Previous results are available in the git history
folder=0
while read line; do
    folder=$(expr 1 + $folder)
    if [ $folder -ge 35 ]
    then
        git rm -r $line
    fi
done <  $ValidationPath/Webpage/folderlist

#setup the commit
echo "Adding"
git add --all
git commit -a -m "CI update: new pages for ${TRAVIS_COMMIT}"

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
