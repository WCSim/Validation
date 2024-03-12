#######Imports#######
import os
import time
"""
Function that checks out the validation webpage branch from git
Arguments:
validation_path = The path to the WCSim validation directory
travis_pull_request = state of the travis pull request ("true" or "false")
"""
def checkout_validation_webpage_branch(validation_path, travis_pull_request, travis_commit):
    os.chdir(validation_path)

    webpage_path = os.path.join(validation_path, "Webpage")

    if not os.path.isdir(webpage_path):
        os.system(f"git clone https://github.com/WCSim/Validation.git --single-branch --depth 1 -b gh-pages ./Webpage")
        os.chdir("Webpage")

        # Add a default user, otherwise git complains
        os.system("git config user.name 'WCSim CI'")
        os.system("git config user.email 'wcsim@wcsim.wcsim'")

        os.chdir("-")

    travis_pull_request = str(travis_pull_request) if travis_pull_request is not None else "false"
    print("Showing travis commit")
    print(travis_commit)
    print("Showing travis pull request")
    print(travis_pull_request)

"""
Function that updates the webpage
Arguments:
validation_path = The path to the WCSim validation directory
travis_commit
GitHubToken
"""
def update_webpage(validation_path, travis_commit, GitHubToken):
    os.chdir(os.path.join(validation_path, "Webpage"))

    # Clean up old folders
    folder = 0
    with open(os.path.join(validation_path, "Webpage", "folderlist"), 'r') as folderlist_file:
        for line in folderlist_file:
            folder += 1
            if folder >= 35:
                os.system(f"git rm -r {line.strip()}")

    # Setup the commit
    print("Adding")
    os.system("git add --all")
    os.system(f"git commit -a -m 'CI update: new pages for {travis_commit}'")

    # Setup a loop to prevent clashes when multiple jobs change the webpage at the same time
    # Make it a for loop, so there isn't an infinite loop
    # 100 attempts, 15 seconds between = 25 minutes of trying
    # The CI is set up such that files will be touched by one job at once,
    # so it's just a matter of keeping pulling until we happen to be at the front of the queue
    for iattempt in range(101):
        # Get the latest version of the webpage
        os.system("git pull --rebase")

        # Attempt to push
        push_command = f"git push https://tdealtry:{GitHubToken}@github.com/WCSim/Validation.git gh-pages"
        if os.system(push_command) == 0:
            break

        # Have a rest before trying again
        time.sleep(15)

"""
Function that adds a line. Taken from RunTests.sh
Arguments:
TESTWEBPAGE= File that contains the test webpage
color = cell color
link = The link to add
text = The text to add
"""
def add_entry(TESTWEBPAGE,color, link, text):
    with open(TESTWEBPAGE, 'a') as f:
        f.write('''
                <tr>
                    <td bgcolor="{}">{}{}</td>
                </tr>
                '''.format(color, link, text))
        
"""
Function to prepare and handle checking for diffs between new and reference. (NOT IN USE YET).
"""
def check_diff(TESTWEBPAGE, diff_path, diff_file, ref_file, test_file, file_type):
    diff_command = f"diff {ref_file} {test_file}"
    diff_output = os.popen(diff_command).read()

    if diff_output:
        add_entry(TESTWEBPAGE, "#FF0000", f"<a href='{diff_file}'>", file_type)
        print(f"{file_type}:")
        print(diff_output)
        with open(f"{diff_file}", "w") as df:
            df.write(diff_output)
        os.system(f"mv {diff_file} {diff_path}")
        return 1 #Exit with a diff found
    elif not os.path.isfile(f"{ref_file}"):
        add_entry(TESTWEBPAGE, "#FF00FF", "", f"Reference {file_type} not found")
    else:
        add_entry(TESTWEBPAGE, "#00FF00", "", f"{file_type} pass")
    return 0 #Exit with no diff found