#!/usr/bin/python3
import os
import WebpageFunctions
import argparse
import json

#Get a set of arguments
parser = argparse.ArgumentParser()
parser.add_argument("--test_num", required=True ,help="The test number to run. This is defined by the line in tests.txt. Leaving it blank defaults to zero and all tests are run.",type=int,default=1)
args = parser.parse_args()

# build the comparison script
ValidationPath = os.getenv("ValidationPath")
os.chdir(ValidationPath)
os.system("make")

#Grab environment variables, if not exisiting, replace with default value.
TRAVIS_PULL_REQUEST = os.getenv("TRAVIS_PULL_REQUEST","false")
TRAVIS_PULL_REQUEST_TITLE = os.getenv("TRAVIS_PULL_REQUEST_TITLE","")
TRAVIS_PULL_REQUEST_LINK = os.getenv("TRAVIS_PULL_REQUEST_LINK","")
TRAVIS_COMMIT = os.getenv("TRAVIS_COMMIT","")

WebpageFunctions.checkout_validation_webpage_branch(ValidationPath,TRAVIS_PULL_REQUEST,TRAVIS_COMMIT)

ret = 0
####### Running tests #######
# Each test has it's own webpage, so lets just build it as we go
TESTDIR=f"{ValidationPath}/Webpage/{TRAVIS_COMMIT}/{args.test_num}"

TESTWEBPAGE = f"{TESTDIR}/index.html"
# First make the directory
os.system(f"mkdir {TESTDIR}")

#Start with the header
with open(f"{ValidationPath}/Webpage/templates/test/header.html", 'r') as header_file:
    header_content = header_file.read()

if TRAVIS_PULL_REQUEST != "false":
    TRAVIS_COMMIT_MESSAGE = f" Pull Request #{TRAVIS_PULL_REQUEST}: {TRAVIS_PULL_REQUEST_TITLE}"
else:
    TRAVIS_COMMIT_MESSAGE = ""

with open(TESTWEBPAGE, 'w') as test_webpage_file:
    test_webpage_file.write(header_content)
    test_webpage_file.write(f"""
    <h2>{TRAVIS_COMMIT}</h2>
    <h3>{TRAVIS_PULL_REQUEST_LINK}{TRAVIS_COMMIT_MESSAGE}</h3>
    """)

# Loop over tests.txt to find the correct job we want to run.
with open('tests.json', 'r') as json_file:
    data = json.load(json_file)


#Grab the right test
values = data[f'Test{args.test_num}']
name = values['name']
test = values['test']
variables = {f'var{i}': values[f'var{i}'] for i in range(1, len(values) - 1)}

print(f"Running test {args.test_num} with name: {name} of type: {test} with variables: {variables}")
# Add the details of the test to the TESTWEBPAGE
with open(TESTWEBPAGE, 'a') as webpage:
    webpage.write(f"\n<h3>{name}</h3>\n")

######### Physics Validation #########
if test == "PhysicsValidation":
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
    rootfilename = f"{variables['var3']}_analysed_wcsimrootevent.root"
    if not os.path.isfile(os.path.join(ValidationPath, 'Compare', 'Reference', rootfilename)):
        WebpageFunctions.add_entry(TESTWEBPAGE,"#FF00FF", "", "Reference file does not exist")
        ret = 1

    #First run WCSim with the chosen mac file.
    isubjob = 0
    wcsim_exit_status = os.system(f"/usr/bin/time -p --output=timetest {ValidationPath}/{variables['var1']} {ValidationPath}/Generate/macReference/{variables['var2']} {variables['var3']}.root |& tee wcsim_run.out")

    # Check the exit status of the previous command
    if wcsim_exit_status != 0:
        WebpageFunctions.add_entry(TESTWEBPAGE,"#FF0000", "", "Failed to run WCSim")
        ret = 1
    else:
        with open("timetest", "r") as timetest_file:
            for line in timetest_file:
                if "user" in line:
                    time = line.split()[1] + " sec"
                    break

        WebpageFunctions.add_entry(TESTWEBPAGE,"#00FF00", "", time)

        # Compare output root files with reference
        wcsim_has_output = 0
        isubjob = 0
        for pmttype in ["wcsimrootevent", "wcsimrootevent2", "wcsimrootevent_OD"]:
            isubjob += 1
            root_filename = f"{variables['var3']}_analysed_{pmttype}.root"

            if os.path.isfile(root_filename):
                wcsim_has_output = 1
                link = f"<a href='{isubjob}/index.html'>"
                if not os.path.isdir(f"{TESTDIR}/{isubjob}"):
                    os.mkdir(f"{TESTDIR}/{isubjob}")
                
                compare_exit_status = os.system(f"{ValidationPath}/Compare/compareroot {ValidationPath}/Webpage/{TRAVIS_COMMIT}/{args.test_num}/{isubjob} {root_filename} {ValidationPath}/Compare/Reference/{root_filename}")
                
                if compare_exit_status != 0:
                    WebpageFunctions.add_entry(TESTWEBPAGE,"#FF0000", link, f"Failed {pmttype} plot comparisons")
                    ret = 1
                else:
                    WebpageFunctions.add_entry(TESTWEBPAGE,"#00FF00", link, f"{pmttype} plot pass")
            else:
                WebpageFunctions.add_entry(TESTWEBPAGE,"#000000", "", f"No {pmttype} in geometry")

        if wcsim_has_output == 0:
            ret = 1


        #Compare the grofile.txt output to the reference.
        #This can almost certainly be streamlined with a function, but just want to make sure it works first :).
        print("Comparing geofile")
        isubjob += 1
        test_file_geo = f"{variables['var4']}"
        ref_file_geo = f"{ValidationPath}/Compare/Reference/{variables['var4']}"
        diff_file_geo = f"{variables['var4']}.diff.txt"
        diff_path = f"{ValidationPath}/Webpage/{TRAVIS_COMMIT}/{args.test_num}/"

        ret = WebpageFunctions.check_diff(TESTWEBPAGE, diff_path, diff_file_geo ,ref_file_geo, test_file_geo, "Geom")

        #Then compare the output bad.txt with the reference.
        print("Comparing badfile")
        isubjob += 1
        test_file_bad = f"{variables['var3']}_bad.txt"
        ref_file_bad = f"{ValidationPath}/Compare/Reference/{test_file_bad}"
        diff_file_bad = f"{variables['var3']}_bad.diff.txt"

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
        ret = WebpageFunctions.check_diff(TESTWEBPAGE, diff_path, diff_file_bad, ref_file_bad, test_file_bad, "bad")

        #Then produce a grep of impossible geometry warnings
        isubjob += 1
        impossiblefilename = f"{variables['var3']}_impossible.txt"

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
            WebpageFunctions.add_entry(TESTWEBPAGE,"#FF0000", f"<a href='{impossiblefilename}'>", "Geometry warnings exist")
            print("Geometry warnings exist:")
            with open(impossiblefilename, "r") as impossible_file:
                print(impossible_file.read())
            os.system(f"mv {impossiblefilename} {ValidationPath}/Webpage/{TRAVIS_COMMIT}/{args.test_num}/")
            ret = 1
        else:
            # If the file is empty, there are no geometry warnings
            WebpageFunctions.add_entry(TESTWEBPAGE,"#00FF00", "", "Geometry warnings pass")

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
#WebpageFunctions.update_webpage(ValidationPath,TRAVIS_COMMIT,"")