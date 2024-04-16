#!/usr/bin/python3

import os
import glob
from common import CommonWebPageFuncs

# Get the logger from CommonWebPageFuncs
cw = CommonWebPageFuncs()
logger = cw.logger

try:
    # Checks out validation webpage branch
    cw.checkout_validation_webpage_branch()

    # More specific stuff here

    run_dir = os.path.join(cw.ValidationPath, "Webpage", cw.GIT_COMMIT)

    # Check if the run directory exists
    if not os.path.isdir(run_dir):
        raise FileNotFoundError(f"Run directory '{run_dir}' does not exist")

    for job_dir in glob.glob(f"{run_dir}/[0-9]*/"):
        try:
            jobnum = int(job_dir.rsplit('/', 2)[-2])
        except ValueError:
            # This happens if we have a directory that starts with a number but has letters in it
            continue

        # If the job directory doesn't exist, skip it
        if not os.path.isdir(job_dir):
            continue

        with open(os.path.join(job_dir, "index.html"), "r") as f:
            colour = f.readlines()[-1]

        with open(os.path.join(run_dir, "index.html"), "r") as f:
            webpage_content = f.read()

        jobnumpad = f"{jobnum:04d}"
        webpage_content = webpage_content.replace(f"'#00FFFF'COLOUR{jobnumpad}", colour)  # Equivalent to the sed command used in the shell script.

        # Put it all together.
        with open(os.path.join(run_dir, "index.html"), "w") as f:
            f.write(webpage_content)

    cw.update_webpage()

except FileNotFoundError as e:
    logger.error(f"An unexpected FileNotFoundError occured: {e}")
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")
