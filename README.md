# Validation

> [!CAUTION]
> You should clone the repository like this
>
> `git clone --depth=1 --single-branch --branch master git@github.com:WCSim/Validation.git`
>
> `--depth=1` gets the current commit
> `--single-branch --branch master` gets only the `master` branch
>
> If you don't follow this advice, you will get a massive history (10s of GB)

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
  * Or, the tests have been cancelled, meaning the colour-setting job is not completed. This happens somewhat frequently (e.g. if someone pushes to a PR branch when CI is already running on that PR branch)

Note that if you rerun a CI after the colours have been set to green/red, the colours will not be updated. This is a bug that should be fixed

## Updating the reference plots

The WCSim/WCSim CI is setup such that, on a new release, a PR on this repo (WCSim/Validation) is automatically created with updated reference plots.
The idea being that every time a WCSim/WCSim PR is merged that changes the distributions, we create a new patch release, such that the reference plots are updated.

Therefore the process is
1. Issue a new WCSim/WCSim release
2. Wait for the reference CI to run
3. From the base of this package, run `./check_commits.sh PRNUM`, to check that all expected commits are included
   * Where `PRNUM` is the PR number of the WCSim/Validation PR that was auto-created
   * This script requires the github command line tools to be installed
4. Check the WCSim/Validation PR diff for the text files, to ensure that there are no major changes to the geometry, warnings that indicate geometry overlaps, etc.
   * This should have been done when checking the WCSim/WCSim PR, before merging into WCSim/WCSim
5. Squash & merge the WCSim/Validation PR
6. Delete the branch `new_ref` WCSim/Validation PR
   * It is **essential** to perform this step. If the `new_ref` branch exists at the start of the reference CI, the git logic in the jobs is such that it will fail
7. Rerun the WCSim/WCSim CI on the latest commit of the repo, to ensure all is coming up green

### If step 3 fails
If the logic of committing to the same branch approximately simulataneously breaks down (again...), then it is recommended to run the stragglers by hand

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
  git clone --depth 1 git@github.com:WCSim/Validation.git -b master --single-branch
  cd Validation
  export ValidationPath=$PWD
  make
  ```
* Ensure WCSim is updated to the latest tagged release `<tag>` (e.g. `v1.12.8`)
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

## More details
* Tests are defined in `test.txt`
  * These link to WCSim config files in `Generate/macReference/`
  * Note that `MakeReference.py` labels tests in the range `[0,N-1]`, whilst `Tests.sh` label tests in the range `[1,N]`. Sorry
* `MakeReference.py` is used to create reference files
  * The output of this is a set of reference files in `Compare/Reference/`
    * Raw vector/number ROOT files, with information extracted from the standard *classed* WCSim ROOT files
    * Text files that specify some information
      * WCSim `geofile_<DETECTORNAME>.txt` files specifying PMT positions
      * `grep`s of the WCSim log files, counting the number of certain warnings (e.g. stuck tracks)
* For webpage creation, this is done in the `gh-pages` branch
  * `SetupWebpages.sh`
    * Sets up a new page (based on the commit hash of the job)
    * Adds an entry to the table in https://wcsim.github.io/Validation/
    * Removes an old entry to the table in https://wcsim.github.io/Validation/
      * Technically it cuts the `html` file to 300 lines. This should be improved, as the bottom entries don't exist
    * Adds an entry to `folderlist` (list of folders = commit hashes) and trims it to 35 entries. Then `git rm`s 
 any folders not in the `folderlist`. This ensures that the webpage does not grow expoentially
    * Pushes to
  * `Tests.sh` does the actual tests (one test is done based on the command line option)
    * Calls `Generate/Generate.sh` for the specified job, to get the same information as we have in `Compare/Reference/`
      * Runs WCSim, saving the log file (temporarily)
      * Converts the WCSim file to the raw vector/number ROOT file with `Reference/daq_readfilemain`
    * Gets the other information we have in `Compare/Reference/`
      * Runs the `grep` tests on the log file
    * Performs difference checks with the reference files
      * ROOT comparison done with `Compare/compareroot`
      * `txt` comparison done with `diff`
    * Builds the webpage for the current job, including setting colours, etc.
    * Leaves a colour code at the bottom of the page, which will be picked up by `FinaliseWebpages.sh`
      * Essentially, this is green if all pass, red if any fail
  * `FinaliseWebpages.sh` runs when all jobs are complete. It
    * Takes the summary colour code for each job, and paints the CI run summary table page the appropriate colours (blue -> red and/or green)


----
## Questions
* Use the issues feature on this repository (preferred)
* Dr. Benjamin Richards (b.richards@qmul.ac.uk)
* Dr. Tom Dealtry (t.dealtry@lancaster.ac.uk)
