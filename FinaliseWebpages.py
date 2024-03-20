#!/usr/bin/python3

import os
import glob
from common import CommonWebPageFuncs

#Initialise the common webpage functions (cw) which in turn initialises all relevant environment variables.
cw = CommonWebPageFuncs()

#Checksout validation webpage branch
cw.checkout_validation_webpage_branch()

# More specific stuff here
run_dir = os.path.join(cw.ValidationPath, "Webpage", cw.GIT_COMMIT)

for job_dir in glob.glob(f"{run_dir}/[0-9]*/"):
    try:
        jobnum = int(job_dir.rsplit('/', 2)[-2])
    except:
        #this happens if we have a directory that starts with a number, but has letters in it
        continue
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


cw.update_webpage()
