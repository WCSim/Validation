#!/usr/bin/python3
import os
import subprocess
from common import CommonWebPageFuncs
import argparse
import json

#Get a set of arguments
parser = argparse.ArgumentParser()
parser.add_argument("--test_num", required=True ,help="The test number to run. This is defined by the Test number in tests.json. This argument is required.",type=int,default=1)
args = parser.parse_args()

# build the comparison script
ValidationPath = os.getenv("ValidationPath")
os.chdir(ValidationPath)
os.system("make")

#Initialise the common object (cw) which in turn initialises all relevant environment variables.
cw = CommonWebPageFuncs()

cw.checkout_validation_webpage_branch()

ret = 0
####### Running tests #######
# Each test has it's own webpage, so lets just build it as we go
TESTDIR=f"{ValidationPath}/Webpage/{cw.GIT_COMMIT}/{args.test_num}"

TESTWEBPAGE = f"{TESTDIR}/index.html"
# First make the directory
if not os.path.isdir(f"{TESTDIR}"):
    print(f"{TESTDIR} already exists. Continue without creating.")
    os.mkdir(f"{TESTDIR}")  

#Start with the header
with open(f"{ValidationPath}/Webpage/templates/test/header.html", 'r') as header_file:
    header_content = header_file.read()

if cw.GIT_PULL_REQUEST != "false":
    GIT_COMMIT_MESSAGE = f" Pull Request #{cw.GIT_PULL_REQUEST}: {cw.GIT_PULL_REQUEST_TITLE}"
else:
    GIT_COMMIT_MESSAGE = ""

with open(TESTWEBPAGE, 'w') as test_webpage_file:
    test_webpage_file.write(header_content)
    test_webpage_file.write(f"""
    <h2>{cw.GIT_COMMIT}</h2>
    <h3>{cw.GIT_PULL_REQUEST_LINK}{GIT_COMMIT_MESSAGE}</h3>
    """)

# Loop over tests.txt to find the correct job we want to run.
with open('tests.json', 'r') as json_file:
    data = json.load(json_file)


#Grab the right test
values = data[f'Test{args.test_num}']
name = values['name']
test = values['test']
variables = {key: value for key, value in values.items() if key not in ['name', 'test']}
print(f"Running test {args.test_num} with name: {name} of type: {test} with variables: {variables}")
# Add the details of the test to the TESTWEBPAGE
with open(TESTWEBPAGE, 'a') as webpage:
    webpage.write(f"\n<h3>{name}</h3>\n")

######### Physics Validation #########
if test == f"{cw.SOFTWARE_NAME}PhysicsValidation":
    # Set up the table of tests
    with open(TESTWEBPAGE, 'a') as f:
        f.write('''
        <p>
        <table  border='1' align='center'>
        <tr>
        <th scope='col'><div align='center'>Tests</div></th>
        </tr>
        ''')

    # Sanity check - ensure the reference file exists
    # This will purposefully fail jobs when new reference mac files are added, until the reference .root files are uploaded
    # Note that this only checks for the first ID PMT type (i.e. `wcsimrootevent` branch of the tree)
    # This should be fine, but will break down if somehow `_2` or `_OD` are the only ones that exist in a future geometry
    #print(variables)
    rootfilename = f"{variables['FileTag']}_analysed_wcsimrootevent.root"
    if not os.path.isfile(os.path.join(ValidationPath, 'Compare', 'Reference', rootfilename)):
        cw.add_entry(TESTWEBPAGE,"#FF00FF", "", "Reference file does not exist")
        ret = 1

    #First run WCSim with the chosen mac file.
    isubjob = 0
    wcsim_exit = subprocess.run(["/usr/bin/time", "-p", "--output=timetest", f"{ValidationPath}/{variables['ScriptName']}", "{ValidationPath}/Generate/macReference/{variables['WCSimMacName']}", "{variables['FileTag']}.root"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    print(wcsim_exit)
    wcsim_exit_status = wcsim_exit.returncode
    logfile = open('wcsim_run.out', 'w')
    while wcsim_exit.poll() is None:
        line = wcsim_exit.stdout.readline()
        logfile.write(line)
    #wcsim_exit_status = os.system(f"/usr/bin/time -p --output=timetest {ValidationPath}/{variables['ScriptName']} {ValidationPath}/Generate/macReference/{variables['WCSimMacName']} {variables['FileTag']}.root |& tee wcsim_run.out")
    print('wcsim_exit_status', wcsim_exit_status, type(wcsim_exit_status))
    
    # Check the exit status of the previous command
    if wcsim_exit_status != 0:
        cw.add_entry(TESTWEBPAGE,"#FF0000", "", "Failed to run WCSim")
        ret = 1
    else:
        with open("timetest", "r") as timetest_file:
            for line in timetest_file:
                if "user" in line:
                    time = line.split()[1] + " sec"
                    break

        cw.add_entry(TESTWEBPAGE,"#00FF00", "", time)

        # Compare output root files with reference
        wcsim_has_output = 0
        isubjob = 0
        for pmttype in ["wcsimrootevent", "wcsimrootevent2", "wcsimrootevent_OD"]:
            isubjob += 1
            root_filename = f"{variables['FileTag']}_analysed_{pmttype}.root"

            if os.path.isfile(root_filename):
                wcsim_has_output = 1
                link = f"<a href='{isubjob}/index.html'>"
                if not os.path.isdir(f"{TESTDIR}/{isubjob}"):
                    os.mkdir(f"{TESTDIR}/{isubjob}")
                
                compare_exit_status = os.system(f"{ValidationPath}/Compare/compareroot {ValidationPath}/Webpage/{cw.GIT_COMMIT}/{args.test_num}/{isubjob} {root_filename} {ValidationPath}/Compare/Reference/{root_filename}")
                print('compare_exit_status', compare_exit_status, type(compare_exit_status))
                if compare_exit_status != 0:
                    cw.add_entry(TESTWEBPAGE,"#FF0000", link, f"Failed {pmttype} plot comparisons")
                    ret = 1
                else:
                    cw.add_entry(TESTWEBPAGE,"#00FF00", link, f"{pmttype} plot pass")
            else:
                cw.add_entry(TESTWEBPAGE,"#000000", "", f"No {pmttype} in geometry")

        print('wcsim_has_output, ret after loop over diffing root files', wcsim_has_output, ret)
        if wcsim_has_output == 0:
            ret = 1


        #Compare the geofile.txt output to the reference.
        #This can almost certainly be streamlined with a function, but just want to make sure it works first :).
        print("Comparing geofile")
        isubjob += 1
        test_file_geo = f"{variables['GeoFileName']}"
        ref_file_geo = f"{ValidationPath}/Compare/Reference/{variables['GeoFileName']}"
        diff_file_geo = f"{variables['GeoFileName']}.diff.txt"
        diff_path = f"{ValidationPath}/Webpage/{cw.GIT_COMMIT}/{args.test_num}/"

        ret += cw.check_diff(TESTWEBPAGE, diff_path, diff_file_geo ,ref_file_geo, test_file_geo, "Geom")

        #Then compare the output bad.txt with the reference.
        print("Comparing badfile")
        isubjob += 1
        test_file_bad = f"{variables['FileTag']}_bad.txt"
        ref_file_bad = f"{ValidationPath}/Compare/Reference/{test_file_bad}"
        diff_file_bad = f"{variables['FileTag']}_bad.diff.txt"

        # Remove the existing badfilename if it exists
        if os.path.isfile(test_file_bad):
            os.remove(test_file_bad)

        # Count occurrences of specified patterns and write to badfilename
        grep_patterns = ["GeomNav1002", "Optical photon is killed because of missing refractive index"]
        with open("wcsim_run.out", "r") as wcsim_run_out:
            with open(test_file_bad, "w") as bad_file:
                for grep_pattern in grep_patterns:
                    grep_count = wcsim_run_out.read().count(grep_pattern)
                    bad_file.write(f"\"{grep_pattern}\" {grep_count}\n")

        # Run the diff command and capture the output
        ret += cw.check_diff(TESTWEBPAGE, diff_path, diff_file_bad, ref_file_bad, test_file_bad, "bad")

        #Then produce a grep of impossible geometry warnings
        isubjob += 1
        impossiblefilename = f"{variables['FileTag']}_impossible.txt"

        # Remove the existing impossiblefilename if it exists
        if os.path.isfile(impossiblefilename):
            os.remove(impossiblefilename)

        # Grep for specified patterns and write to impossiblefilename
        grep_patterns = ["IMPOSSIBLE GEOMETRY", "*** G4Exception : GeomVol1002"]
        with open("wcsim_run.out", "r") as wcsim_run_out:
            with open(impossiblefilename, "w") as impossible_file:
                for grep_pattern in grep_patterns:
                    os.popen(f"grep \"{grep_pattern}\" wcsim_run.out >> {impossiblefilename}")

        # Check if the impossiblefilename is not empty
        if os.path.getsize(impossiblefilename) > 0:
            # If the file is not empty, there are geometry warnings
            cw.add_entry(TESTWEBPAGE,"#FF0000", f"<a href='{impossiblefilename}'>", "Geometry warnings exist")
            print("Geometry warnings exist:")
            with open(impossiblefilename, "r") as impossible_file:
                print(impossible_file.read())
            os.system(f"mv {impossiblefilename} {ValidationPath}/Webpage/{cw.GIT_COMMIT}/{args.test_num}/")
            ret = 1
        else:
            # If the file is empty, there are no geometry warnings
            cw.add_entry(TESTWEBPAGE,"#00FF00", "", "Geometry warnings pass")

#Out of the loop now, no more lines to read.
# Add footer to finish the webpage
# A lot of IO here, can it be reduced? (Files aren't large so not a massive problem).
with open(f"{ValidationPath}/Webpage/templates/test/footer.html", "r") as footer_template:
    footer_content = footer_template.read()

with open(TESTWEBPAGE, "a") as webpage_file:
    webpage_file.write(footer_content)

# Add color code at the bottom for the list of jobs page
if ret == 0:
    print("Finishing writing webpage file. Nothing failed!")
    with open(TESTWEBPAGE, "a") as webpage_file:
        webpage_file.write("#00FF00\n")
else:
    print("Finishing writing webpage file. Something failed!")
    with open(TESTWEBPAGE, "a") as webpage_file:
        webpage_file.write("#FF0000\n")

#Update the webpage.
#This causes all sorts of crazy stuff to happen for me! Doesn't work at the moment
cw.update_webpage()
