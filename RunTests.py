#!/usr/bin/python3
import os
import subprocess
import argparse
import json
import sys
from common import CommonWebPageFuncs

def create_test_webpage_header(ValidationPath):
    '''
    Reads the header content from a template file and returns it.

    Args:
        ValidationPath (str): The path to the directory containing the template files.

    Returns:
        str: The content of the header HTML file.

    Raises:
        FileNotFoundError: If the header HTML file is not found in the specified directory.
    '''
    try:
        with open(f"{ValidationPath}/Webpage/templates/test/header.html", 'r') as header_file:
            header_content = header_file.read()
    except FileNotFoundError:
            raise FileNotFoundError(f" File {ValidationPath}/Webpage/templates/test/header.html could not be found")
    return header_content

def create_test_webpage_footer(ValidationPath):
    '''
    Reads the footer content from a template file and returns it.

    Args:
        ValidationPath (str): The path to the directory containing the template files.

    Returns:
        str: The content of the footer HTML file.

    Raises:
        FileNotFoundError: If the footer HTML file is not found in the specified directory.
    '''
    try: 
        with open(f"{ValidationPath}/Webpage/templates/test/footer.html", "r") as footer_template:
            footer_content = footer_template.read()
    except FileNotFoundError:
        raise FileNotFoundError(f" File {ValidationPath}/Webpage/templates/test/footer.html not found")
    return footer_content

def create_test_webpage(test_dir, header_content, GIT_COMMIT_MESSAGE, GIT_COMMIT, GIT_PULL_REQUEST_LINK):
    '''
    Creates the test webpage where the outcome of the tests are written to.
    The footer is not written to the webpage here as the test info needs to be written to the webpage beforehand.

    Args:
        test_dir (str): The directory where the test webpage will be created.
        header_content (str): The content of the header HTML file to be included in the webpage.
        GIT_COMMIT_MESSAGE (str): The message associated with the Git commit.
        GIT_COMMIT (str): The identifier of the Git commit.
        GIT_PULL_REQUEST_LINK (str): The link to the associated Git pull request.

    Returns:
        str: The path to the created test webpage file.

    Raises:
        Exception: If there is any failure in creating the test webpage.
    '''
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

def check_reference_file(common_funcs, test_webpage, test_variables, debug):
    '''
    First test.
    Checks if a reference file exists. Returns 1 if it does not i.e. the test has failed.

    Args:
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.
        test_variables (dict): A dictionary containing variables relevant to the test.

    Returns:
        int: 1 if the reference file does not exist (indicating test failure), otherwise 0.

    Comments:
        This function does not catch errors explicitly, but it could be extended to do so.
        The current implementation logs the absence of the reference file as a test failure, which was the previous behavior.
    '''
    ret = 0
    rootfilename = f"{test_variables['FileTag']}_analysed_wcsimrootevent.root"
    if not os.path.isfile(rootfilename):
        common_funcs.add_entry(test_webpage, "#FF00FF", "", "Reference file does not exist")
        ret = 1
    if debug:
        print(f"Return value after check_reference_file: {ret}")
    return ret

def run_wcsim(variables, common_funcs, test_webpage, debug):
    '''
    Second test.
    Runs WCSim, checks if it has ran successfully and writes the output to a log file for use in later tests.
    Test fails if WCSim fails to run.

    Args:
        variables (dict): A dictionary containing variables relevant to the test.
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.

    Returns:
        int: 0 if WCSim runs successfully, otherwise raises an exception.

    Raises:
        subprocess.CalledProcessError: If the subprocess call to run WCSim fails.
    '''
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
        if debug:
            print(f"Return value after wcsim_exit: 0")
        return 0

    except subprocess.CalledProcessError as e:
        # If the subprocess call fails, handle the exception
        common_funcs.add_entry(test_webpage, "#FF0000", "", "Failed to run WCSim")
        raise subprocess.CalledProcessError(f"Failed to run WCSim. Return code: {e.returncode}.\nOutput: {e.output.decode()}")



def compare_root_files(common_funcs, test_webpage, test_dir, variables, test_num, debug):
    '''
    Third test.
    Compares the output root files with the reference root files using a custom comparer tool.
    It iterates over different types of PMT files, performs the comparison, and logs the results on the test webpage.
    If any comparison fails or if no output root file is found, it returns 1 indicating test failure.

    Args:
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.
        test_dir (str): The directory where the test output and comparison results will be stored.
        variables (dict): A dictionary containing variables relevant to the test.
        test_num (int): The number of the test being performed.

    Returns:
        int: 0 if all comparisons pass, 1 if any comparison fails.

    Raises:
        Exception: If an unexpected error occurs during the comparison process.
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
    except Exception as e:
        raise Exception(f"Unxpected error occured when comparing the root files: {e}")
    if debug:
        print(f"Return value after compare_root_files: {ret}")
    return ret

def compare_geofile(common_funcs, test_webpage, variables, test_num, debug):
    '''
    Fourth test.
    Compares the output geometry file from WCSim with the reference geometry file.
    It uses the custom check_diff function to perform the comparison.
    If a difference is found, it logs the result on the test webpage and returns 1, indicating test failure.

    Args:
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.
        variables (dict): A dictionary containing variables relevant to the test.
        test_num (int): The number of the test being performed.

    Returns:
        int: 1 if a difference is found between the geometry files, otherwise 0.

    Raises:
        Exception: If an unexpected error occurs during the comparison process.
    '''
    try:
        ret = 0
        test_file_geo = f"{variables['GeoFileName']}"
        ref_file_geo = f"{common_funcs.ValidationPath}/Compare/Reference/{variables['GeoFileName']}"
        diff_file_geo = f"{variables['GeoFileName']}.diff.txt"
        diff_path = f"{common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/"
        ret += common_funcs.check_diff(test_webpage, diff_path, diff_file_geo, ref_file_geo, test_file_geo, "Geom")
    except Exception as e:
        raise Exception(f"Unexpected error occured when comparing the geometry files: {e}")
    if debug:
        print(f"Return value after compare_geofile: {ret}")
    return ret

def compare_badfile(common_funcs, test_webpage, variables, test_num, debug):
    '''
    Fifth test.
    Creates a 'bad' file containing specific patterns extracted from wcsim_run.out.
    It then compares this 'bad' file with the reference 'bad' file using the check_diff function.
    If a difference is found, it logs the result on the test webpage and returns 1, indicating test failure.

    Args:
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.
        variables (dict): A dictionary containing variables relevant to the test.
        test_num (int): The number of the test being performed.

    Returns:
        int: 1 if a difference is found between the 'bad' files, otherwise 0.

    Raises:
        FileNotFoundError: If a required file does not exist.
        Exception: If an unexpected error occurs during the comparison process.
    '''
    try:
        ret = 0
        test_file_bad = f"{variables['FileTag']}_bad.txt"
        ref_file_bad = f"{common_funcs.ValidationPath}/Compare/Reference/{test_file_bad}"
        diff_file_bad = f"{variables['FileTag']}_bad.diff.txt"
        diff_path = f"{common_funcs.ValidationPath}/Webpage/{common_funcs.GIT_COMMIT}/{test_num}/"

        if os.path.isfile(test_file_bad):
            os.remove(test_file_bad)

        grep_patterns = ["GeomNav1002", "Optical photon is killed because of missing refractive index"]

        #Check if wcsim_run.out exists
        if not os.path.isfile("wcsim_run.out"):
            raise FileNotFoundError("File wcsim_run.out does not exist.")

        with open("wcsim_run.out", "r") as wcsim_run_out:
            with open(test_file_bad, "w") as bad_file:
                wcsim_run_out_str = wcsim_run_out.read()
                for grep_pattern in grep_patterns:
                    grep_count = wcsim_run_out_str.count(grep_pattern)
                    bad_file.write(f"\"{grep_pattern}\" {grep_count}\n")
        ret += common_funcs.check_diff(test_webpage, diff_path, diff_file_bad, ref_file_bad, test_file_bad, "bad")

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Unexpected FileNotFoundError when comparing bad files: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error when comparing bad files: {e}")
    if debug:
        print(f"Return value after compare_badfile: {ret}")
    return ret

def check_impossible_geometry(common_funcs, test_webpage, variables, test_num, debug):
    '''
    Sixth test.
    Creates an 'impossible' geometry file containing specific patterns extracted from wcsim_run.out.
    It then checks if the file is empty or not and logs the result on the test webpage.
    If geometry warnings exist, it moves the file to the appropriate directory and returns 1, indicating test failure.

    Args:
        common_funcs (object): An object containing common functions used in the testing process.
        test_webpage (str): The path to the test webpage where test results will be recorded.
        variables (dict): A dictionary containing variables relevant to the test.
        test_num (int): The number of the test being performed.

    Returns:
        int: 1 if geometry warnings exist, otherwise 0.

    Raises:
        FileNotFoundError: If a required file does not exist.
        Exception: If an unexpected error occurs during the process.
    '''
    ret = 0
    impossiblefilename = f"{variables['FileTag']}_impossible.txt"
    try:
        if os.path.isfile(impossiblefilename):
            os.remove(impossiblefilename)

        grep_patterns = ["IMPOSSIBLE GEOMETRY", "*** G4Exception : GeomVol1002"]
        
        # Check if wcsim_run.out exists
        if not os.path.isfile("wcsim_run.out"):
            raise FileNotFoundError("File wcsim_run.out does not exist.")

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
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Unexpected FileNotFoundError when checking impossible geometry: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error occurred when checking impossible geometry: {e}")
    if debug:
        print(f"Return value after check_impossible_geometry: {ret}")
    return ret

def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--test_num", required=True, help="The test number to run.", type=int, default=1)
        parser.add_argument("--debug", help="Debug tag that prints out debug statements in the script.", action="store_true")
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
        
        #Run all of the physics validation tests in order. The order of tests is important, WCSim should be run before file tests.
        if test_type == f"{common_funcs.SOFTWARE_NAME}PhysicsValidation":
            ret = check_reference_file(common_funcs, test_webpage, test_variables, args.debug)
            ret += run_wcsim(test_variables, common_funcs, test_webpage, args.debug)
            ret += compare_root_files(common_funcs, test_webpage, test_dir, test_variables, args.test_num, args.debug)
            ret += compare_geofile(common_funcs, test_webpage, test_variables, args.test_num, args.debug)
            ret += compare_badfile(common_funcs, test_webpage, test_variables, args.test_num, args.debug)
            ret += check_impossible_geometry(common_funcs, test_webpage, test_variables, args.test_num, args.debug)




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
