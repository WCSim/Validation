# Validation

Validation output is displayed here https://wcsim.github.io/Validation/

Note: Initial compilation build and simple excecution tests will run in about 5 mins. The validation tests will take longer (up to 2 hours) with results being updated to the webpage when finished.

* If test fields are green:
  * Then tests have passed
  * Log files and physics output can be retrived from the text link
* If tests fields are red:
  * Then test have failed
  * For physics tests validation plots can be accessed from the link. Incorrect plots will be shown with the text "Error!!!". The stars indicate the expected value, and the lines the submission results.
* If test fields are blue:
  * Then tests are still ongoing. Please wait for output
    * Note that the colours are updated only when all jobs are finished. You may be able to get a sneak preview of quicker tests (e.g. 5 MeV electron) before the slower tests complete (e.g. 500 MeV muon)

Note that if you rerun a CI after the colours have been set to green/red, the colours will not be updated. This is a bug that should be fixed

## Updating the reference plots

The WCSim/WCSim CI is setup such that on a new release, a PR on this repo (WCSim/Validation) is automatically created with updated reference plots.
The idea being that every time a WCSim/WCSim PR is merged that changes the distributions, we create a new patch release, such that the reference plots are updated.

Therefore the process is
1. Issue a new WCSim/WCSim release
2. Wait for the CI to run
3. From the base of this package, run `./check_commits.sh PRNUM`, to check that all expected commits are included
   * Where `PRNUM` is the PR number of the WCSim/Validation PR that was auto-created
   * This script requires the github command line tools to be installed
4. Check the WCSim/Validation PR diff for the text files, to ensure that there are no major changes to the geometry, warnings that indicate geometry overlaps, etc.
   * This should have been done when checking the WCSim/WCSim PR, before merging into WCSim/WCSim
5. Squash & merge the WCSim/Validation PR
6. Delete the branch `new_ref` WCSim/Validation PR
7. Rerun the WCSim/WCSim CI on the latest commit of the repo, to ensure all is coming up green

### If step 3 fails
If the logic of committing to the same branch approximately simulataneously breaks down again, then it is recommended to run the stragglers by hand

Say the jobs missing looks like
```
2 jobs missing: [3, 20]
```

It is recommended to make the validation plots within a docker container, so that the dependencies are running the same versions that the automated tests will use i.e.
```bash
docker run -it --name=WCSimValid docker://ghcr.io/hyperk/hk-software:0.0.2
```

Then
* Ensure Validation is updated to the latest release
  ```bash
  git clone git@github.com:WCSim/Validation.git
  cd Validation
  export ValidationPath=$PWD
  make
  ```
* Ensure WCSim is updated to the latest release
  ```bash
  cd $ValidationPath/..
  git clone git@github.com:WCSim/WCSim.git WCSimRelease
  cd WCSimRelease
  git switch --detach <tag>
  $ValidationPath/build.sh
  source install/bin/this_wcsim.sh
  ```
* Run the reference file maker script, for the missing jobs e.g.
  ```bash
  cd $ValidationPath
  python3 MakeReference.py --job-number 3 20
  ```
* Return to step 3

----
For any questions contact Dr. Benjamin Richards (b.richards@qmul.ac.uk), Dr. Tom Dealtry (t.dealtry@lancaster.ac.uk), or (preffered) use the issues feature on this repository
