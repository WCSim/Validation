#!/usr/bin/python3
import os
import subprocess
import argparse
import json
import sys
from common import CommonWebPageFuncs

def create_test_webpage_header(ValidationPath):
    try:
        with open(f"{ValidationPath}/Webpage/templates/test/header.html", 'r') as header_file:
            header_content = header_file.read()
    except FileNotFoundError:
            raise FileNotFoundError(f" File {ValidationPath}/Webpage/templates/test/header.html could not be found")
    return header_content

def create_test_webpage_footer(ValidationPath):
    try: 
        with open(f"{ValidationPath}/Webpage/templates/test/footer.html", "r") as footer_template:
            footer_content = footer_template.read()
    except FileNotFoundError:
        raise FileNotFoundError(f" File {ValidationPath}/Webpage/templates/test/footer.html not found")
    return footer_content

def create_test_webpage(test_dir, header_content, GIT_COMMIT_MESSAGE, GIT_COMMIT, GIT_PULL_REQUEST_LINK):
    try:
        test_webpage = os.path.join(test_dir, "index.html")
        with open(test_webpage, 'w') as test_webpage_file:
            test_webpage_file.write(header_content)
            test_webpage_file.write(f"""
            <h2>{GIT_COMMIT}</h2>
            <h3>{GIT_PULL_REQUEST_LINK}{GIT_COMMIT_MESSAGE}</h3>
            """)
    except Exception:
        raise Exception("Failed to create test webpage")

    return test_webpage

def check_reference_file(common_funcs, test_webpage, test_variables): 
    rootfilename = f"{test_variables['FileTag']}_analysed_wcsimrootevent.root"
    if not os.path.isfile(rootfilename):
        common_funcs.add_entry(test_webpage, "#FF00FF", "", "Reference file does not exist") #Not clear with this, seems like it still needs to run even if reference file not found.
        return 1
    return 0

def run_wcsim(variables, common_funcs, test_webpage):
    try:
        wcsim_exit = subprocess.run(["/usr/bin/time", "-p", "--output=timetest", f"{common_funcs.ValidationPath}/{variables['ScriptName']}", f"{common_funcs.ValidationPath}/Generate/macReference/{variables['WCSimMacName']}", f"{variables['FileTag']}.root"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        
        # Write the command and its output to a log file
        with open('wcsim_run.out', 'w') as logfile:
            logfile.write(wcsim_exit.stdout.decode())

        print(wcsim_exit.stdout.decode())

        # Parse the timing information
        with open("timetest", "r") as timetest_file:
            for line in timetest_file:
                if "user" in line:
                    time = line.split()[1] + " sec"
                    break

        common_funcs.add_entry(test_webpage, "#00FF00", "", time)
        return 0

    except subprocess.CalledProcessError as e:
        # If the subprocess call fails, handle the exception
        common_funcs.add_entry(test_webpage, "#FF0000", "", "Failed to run WCSim")
        raise subprocess.CalledProcessError(f"Failed to run WCSim. Return code: {e.returncode}.\nOutput: {e.output.decode()}")



def compare_root_files(common_funcs, test_webpage, test_dir, variables, test_num):
    '''
    Compare output root file with the reference file
    '''
    try:
        ret = 0
        wcsim_has_output = 0
        isubjob = 0
        for pmttype in ["wcsimrootevent", "wcsimrootevent2", "wcsimrootevent_OD"]:
            isubjob += 1
            root_filename = f"{variables['FileTag']}_analysed_{pmttype}.root"
            if os.path.isfile(root_filename):
                wcsim_has_output = 1
                link = f"<a href='{isubjob}/index.html'>"
                if not os.path.isdir(f"{test_dir}/{isubjob}"):
                    os.mkdir(f"{test_dir}/{isubjob}")
                compare_exit_status = os.system(f"{common_funcs.ValidationPath}/Compare/compareroot {common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/{isubjob} {root_filename} {common_funcs.ValidationPath}/Compare/Reference/{root_filename}")
                print('compare_exit_status', compare_exit_status, type(compare_exit_status))
                if compare_exit_status != 0:
                    common_funcs.add_entry(test_webpage, "#FF0000", link, f"Failed {pmttype} plot comparisons")
                    ret = 1
                else:
                    common_funcs.add_entry(test_webpage, "#00FF00", link, f"{pmttype} plot pass")
            else:
                common_funcs.add_entry(test_webpage, "#000000", "", f"No {pmttype} in geometry")

        print('wcsim_has_output, ret after loop over diffing root files', wcsim_has_output, ret)
        if wcsim_has_output == 0:
            ret = 1
    except Exception:
        raise Exception("Failed to compare the root files")
    return ret

def compare_geofile(common_funcs, test_webpage, variables, test_num):
    ret = 0
    test_file_geo = f"{variables['GeoFileName']}"
    ref_file_geo = f"{common_funcs.ValidationPath}/Compare/Reference/{variables['GeoFileName']}"
    diff_file_geo = f"{variables['GeoFileName']}.diff.txt"
    diff_path = f"{common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/"
    ret += common_funcs.check_diff(test_webpage, diff_path, diff_file_geo, ref_file_geo, test_file_geo, "Geom")
    return ret

def compare_badfile(common_funcs, test_webpage, variables, test_num):
    ret = 0
    test_file_bad = f"{variables['FileTag']}_bad.txt"
    ref_file_bad = f"{common_funcs.ValidationPath}/Compare/Reference/{test_file_bad}"
    diff_file_bad = f"{variables['FileTag']}_bad.diff.txt"
    diff_path = f"{common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/"

    if os.path.isfile(test_file_bad):
        os.remove(test_file_bad)

    grep_patterns = ["GeomNav1002", "Optical photon is killed because of missing refractive index"]
    with open("wcsim_run.out", "r") as wcsim_run_out:
        with open(test_file_bad, "w") as bad_file:
            wcsim_run_out_str = wcsim_run_out.read()
            for grep_pattern in grep_patterns:
                grep_count = wcsim_run_out_str.count(grep_pattern)
                bad_file.write(f"\"{grep_pattern}\" {grep_count}\n")
    ret += common_funcs.check_diff(test_webpage, diff_path, diff_file_bad, ref_file_bad, test_file_bad, "bad")
    return ret

def check_impossible_geometry(common_funcs, test_webpage, variables, test_num):
    ret = 0
    impossiblefilename = f"{variables['FileTag']}_impossible.txt"
    if os.path.isfile(impossiblefilename):
        os.remove(impossiblefilename)

    grep_patterns = ["IMPOSSIBLE GEOMETRY", "*** G4Exception : GeomVol1002"]
    with open("wcsim_run.out", "r") as wcsim_run_out:
        with open(impossiblefilename, "w") as impossible_file:
            for grep_pattern in grep_patterns:
                os.popen(f"grep \"{grep_pattern}\" wcsim_run.out >> {impossiblefilename}")

    if os.path.getsize(impossiblefilename) > 0:
        common_funcs.add_entry(test_webpage, "#FF0000", f"<a href='{impossiblefilename}'>", "Geometry warnings exist")
        print("Geometry warnings exist:")
        with open(impossiblefilename, "r") as impossible_file:
            print(impossible_file.read())
        os.system(f"mv {impossiblefilename} {common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/")
        ret = 1
    else:
        common_funcs.add_entry(test_webpage, "#00FF00", "", "Geometry warnings pass")
    return ret

def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--test_num", required=True, help="The test number to run.", type=int, default=1)
        args = parser.parse_args()

        common_funcs = CommonWebPageFuncs()
        logger = common_funcs.logger
        test_dir = f"{common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{args.test_num}"

        # Checkout validation repository
        common_funcs.checkout_validation_webpage_branch()

        # build the comparison script
        try:
            subprocess.run(["make"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(f"Failed to build the comparison script. Return code: {e.returncode}.\nOutput: {e.output.decode()}")
        
        # run from the software location, in order to get the relevant data files (if required)
        #os.chdir('/opt/WCSim/install')

        if common_funcs.GIT_PULL_REQUEST != "false":
            GIT_COMMIT_MESSAGE = f" Pull Request #{common_funcs.GIT_PULL_REQUEST}: {common_funcs.GIT_PULL_REQUEST_TITLE}"
        else:
            GIT_COMMIT_MESSAGE = ""

        if not os.path.isdir(test_dir):
            os.makedirs(test_dir)

        header_content = create_test_webpage_header(common_funcs.ValidationPath)
        footer_content = create_test_webpage_footer(common_funcs.ValidationPath)
        test_webpage = create_test_webpage(test_dir, header_content, GIT_COMMIT_MESSAGE, common_funcs.GIT_COMMIT, common_funcs.GIT_PULL_REQUEST_LINK)

        with open(os.path.join(common_funcs.ValidationPath, 'tests.json'), 'r') as json_file:
            data = json.load(json_file)

        values = data[f'Test{args.test_num}']
        test_name = values['name']
        test_type = values['test']
        test_variables = {key: value for key, value in values.items() if key not in ['name', 'test']}

        print(f"Running test {args.test_num} with name: {test_name} of type: {test_type} with variables: {test_variables}")

        with open(test_webpage, 'a') as webpage:
            webpage.write(f"\n<h3>{test_name}</h3>\n")


        #Setup the table of tests
        with open(test_webpage, 'a') as f:
            f.write('''
            <p>
            <table  border='1' align='center'>
            <tr>
            <th scope='col'><div align='center'>Tests</div></th>
            </tr>
            ''')

        #Run all of the physics validation tests in order. The order of tests is important, WCSim should be run before other checks.
        if test_type == f"{common_funcs.SOFTWARE_NAME}PhysicsValidation":
            ret = check_reference_file(common_funcs, test_webpage, test_variables)
            ret += run_wcsim(test_variables, common_funcs, test_webpage)
            ret += compare_root_files(common_funcs, test_webpage, test_dir, test_variables, args.test_num,)
            ret += compare_geofile(common_funcs, test_webpage, test_variables, args.test_num)
            ret += compare_badfile(common_funcs, test_webpage, test_variables, args.test_num)
            ret += check_impossible_geometry(common_funcs, test_webpage, test_variables, args.test_num)



        # Add the footer and...
        # Add color code at the bottom for the list of jobs page
        if ret == 0:
            print("Finishing writing webpage file. Nothing failed!")
            with open(test_webpage, "a") as webpage_file:
                webpage_file.write(footer_content)
                webpage_file.write("#00FF00\n")
        else:
            print("Finishing writing webpage file. Something failed!")
            with open(test_webpage, "a") as webpage_file:
                webpage_file.write(footer_content)
                webpage_file.write("#FF0000\n")

        common_funcs.update_webpage()
        
        if ret != 0:
            sys.exit(-1)
    
    except FileNotFoundError as e:
        logger.error(f"File not found error in RunTests: {e}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running subprocess in RunTests: Return code {e.returncode}, Output: {e.output.decode()}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred in RunTests: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()
