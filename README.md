# Validation

Validation output is displayed here https://wcsim.github.io/Validation/

Note: Initial compilation build and simple excecution tests will run in about 5 mins. The validation tests will take longer with results being updated to the webpage when finished.

*** If test fields are green with the excecution time displayed: 
Then tests have passed (logs files or physics output can be retrived form the text link)

*** If tests fields are red with "Failed" text: 
Then test have failed (For physics tests validation plots can be accessed from the link. Incorrect plots will be shown with the text "Error!!!". The stars indicate the expected value, and the lines the submission results.)

*** If fields have text similar to "uwr89yh32hrhh3903heText2": 
Then those tests are not yet complete please wait for output

## Updating the reference plots

It is recommended to make the validation plots within a docker container, so that the dependencies are running the same versions that the automated tests will use i.e.
```bash
docker run -it --name=WCSimValid wcsim/wcsim:develop
```
Set  GITHUBUSERNAME variable to your github username e.g.
```bash
export GITHUBUSERNAME=tdealtry
```
Then you'll want to run these commands
```bash
#Make sure WCSim is up-to-date
cd $WCSIMDIR
git pull origin develop
#Get the Validation package
cd /opt/HyperK/
git clone git@github.com:WCSim/Validation.git #cloning from WCSim ensures you're up-to-date without conflicts
cd Validation/
git remote add me git@github.com:$GITHUBUSERNAME/Validation.git #this is where you'll push to
#Build the Validation tools
export LD_LIBRARY_PATH=$WCSIMDIR:$LD_LIBRARY_PATH
make
#Make a new branch
git checkout -b update_reference
#Update the reference plots
./MakeReference.sh
#Commit the new `.root` files
git add Compare/Reference/analysed_*root Compare/Reference/WCSimSHA
git ci #write why the reference plots have changed e.g. link to WCSim/WCSim PR number
#Push to your repo
git push me update_reference
```
Then finally, visit https://github.com/WCSim/Validation (or follow the link from the last command above) to submit a PR

----
For any questions contact Dr. Benjamin Richards (b.richards@qmul.ac.uk), Dr. Tom Dealtry (t.dealtry@lancaster.ac.uk), or use the issues feature on this repository