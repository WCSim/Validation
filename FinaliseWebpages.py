#!/usr/bin/python3

import os
import WebpageFunctions

#Grab environment variables, if not exisiting, replace with default value.
ValidationPath = os.getenv("ValidationPath")
TRAVIS_PULL_REQUEST = os.getenv("TRAVIS_PULL_REQUEST","false")
TRAVIS_PULL_REQUEST_TITLE = os.getenv("TRAVIS_PULL_REQUEST_TITLE","")
TRAVIS_PULL_REQUEST_LINK = os.getenv("TRAVIS_PULL_REQUEST_LINK","")
TRAVIS_COMMIT = os.getenv("TRAVIS_COMMIT","")
GITHUBTOKEN = os.getenv("GITHUBTOKEN","")

#Common function, should add as such.
WebpageFunctions.checkout_validation_webpage_branch(ValidationPath,TRAVIS_PULL_REQUEST,TRAVIS_COMMIT)

# More specific stuff here
run_dir = os.path.join(ValidationPath, "Webpage", TRAVIS_COMMIT)

for jobnum in range(1, 101):
    job_dir = os.path.join(run_dir, str(jobnum))
    #If the job directory doesn't exist, die.
    if not os.path.isdir(job_dir):
        break # Changed from boolean as 'break' makes code easier to use imo.

    with open(os.path.join(job_dir, "index.html"), "r") as f:
        colour = f.readlines()[-1]

    with open(os.path.join(run_dir, "index.html"), "r") as f:
        webpage_content = f.read()

    jobnumpad = f"{jobnum:04d}"
    webpage_content = webpage_content.replace(f"'#00FFFF'COLOUR{jobnumpad}", colour) # Equivalent to the sed command used in the shell script.

    #Put it all together.
    with open(os.path.join(run_dir, "index.html"), "w") as f:
        f.write(webpage_content)


WebpageFunctions.update_webpage(ValidationPath, TRAVIS_COMMIT, GITHUBTOKEN)