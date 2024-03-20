#####IMPORTS######
import os
import time
import json

class CommonWebPageFuncs:
    def __init__(self):
        #Could these come from a config? Also, inconsistent naming scheme. Please change.
        self.ValidationPath = os.getenv("ValidationPath")
        self.GIT_PULL_REQUEST = os.getenv("GIT_PULL_REQUEST", "false")
        self.GIT_PULL_REQUEST_TITLE = os.getenv("GIT_PULL_REQUEST_TITLE", "")
        self.GIT_PULL_REQUEST_LINK = os.getenv("GIT_PULL_REQUEST_LINK", "")
        self.GIT_COMMIT = os.getenv("GIT_COMMIT", "")

        #Some variables to read from a config file - this is set up as an example. May want to expand this later.
        with open("git_setup.json") as config_file: #THis config file can be passed as an argument to the class init, do we want to do this?
            data = json.load(config_file)

        #Git config
        self.GIT_USER = data["Commit"]["Username"]
        self.GIT_EMAIL = data["Commit"]["Email"]
        self.GIT_TOKEN = data["Commit"]["Token"]
        #Validation setup
        self.WEBPAGE_BRANCH = data["Validation"]["WebPageBranch"]
        self.WEBPAGE_FOLDER = data["Validation"]["WebPageFolder"]
        self.VALIDATION_GIT_PATH = data["Validation"]["Path"]
        self.VALIDATION_GIT_BRANCH = data["Validation"]["CodeBranch"]
        #Software setup
        self.SOFTWARE_NAME = data["Software"]["Name"]
        self.SOFTWARE_GIT_PATH = data["Software"]["Path"]
        self.SOFTWARE_GIT_BRANCH = data["Software"]["Branch"]
        
        
    def checkout_validation_webpage_branch(self):
        """
        Function that checks out the validation webpage branch from git.

        The function checks if the Webpage directory exists within ValidationPath. If not, it clones the gh-pages branch of the Validation repository from GitHub into the Webpage directory.
        Additionally, it sets up default git user configurations if not already configured.

        Arguments:
        - self.ValidationPath: The path to the WCSim validation directory.
        - self.GIT_PULL_REQUEST: The state of the GIT CI pull request ("true" or "false").
        - self.GIT_COMMIT: The commit ID of the GIT CI build.
        """

        os.chdir(self.ValidationPath)

        webpage_path = os.path.join(self.ValidationPath, "Webpage")

        if not os.path.isdir(webpage_path):
            os.system(f"git clone https://{self.VALIDATION_GIT_PATH} --single-branch --depth 1 -b {self.WEBPAGE_BRANCH} {self.WEBPAGE_FOLDER}")
            os.chdir("Webpage")

            # Add a default user, otherwise git complains
            os.system("git config user.name 'WCSim CI'")
            os.system("git config user.email 'wcsim@wcsim.wcsim'")

            os.chdir(f"{self.ValidationPath}")

        self.GIT_PULL_REQUEST = str(self.GIT_PULL_REQUEST) if self.GIT_PULL_REQUEST is not None else "false"
        print("Showing GIT commit")
        print(self.GIT_COMMIT)
        print("Showing GIT pull request")
        print(self.GIT_PULL_REQUEST)

    def update_webpage(self):
        """
        Function that updates the webpage.

        This function cleans up old folders, adds and commits changes to the git repository, and pushes changes to the remote repository.
        It includes a loop to handle potential conflicts when multiple jobs attempt to change the webpage simultaneously.

        Arguments:
        - self.ValidationPath: The path to the WCSim validation directory.
        - self.GIT_COMMIT: The commit ID of the GIT CI build.
        - self.GIT_TOKEN: The GitHub token for authentication.
        """

        os.chdir(os.path.join(self.ValidationPath, "Webpage"))

        # Clean up old folders
        folder = 0
        with open(os.path.join(self.ValidationPath, "Webpage", "folderlist"), 'r') as folderlist_file:
            for line in folderlist_file:
                folder += 1
                if folder >= 35:
                    os.system(f"git rm -r {line.strip()}")

        # Setup the commit
        print("Adding")
        os.system("git add --all")
        os.system(f"git commit -a -m 'CI update: new pages for {self.GIT_COMMIT}'")

        # Setup a loop to prevent clashes when multiple jobs change the webpage at the same time
        # Make it a for loop, so there isn't an infinite loop
        # 100 attempts, 15 seconds between = 25 minutes of trying
        # The CI is set up such that files will be touched by one job at once,
        # so it's just a matter of keeping pulling until we happen to be at the front of the queue
        for iattempt in range(101):
            # Get the latest version of the webpage
            os.system("git pull --rebase")

            # Attempt to push
            push_command = f"git push https://{self.GIT_USER}:{self.GIT_TOKEN}@{self.VALIDATION_GIT_PATH} {self.WEBPAGE_BRANCH}"
            if os.system(push_command) == 0:
                break

            # Have a rest before trying again
            time.sleep(15)

    def add_entry(self, TESTWEBPAGE, color, link, text):
        """
        Function to add an entry to a test webpage.

        This function appends an HTML table row to a specified test webpage file.

        Arguments:
        - TESTWEBPAGE: The file path of the test webpage.
        - color: The background color of the table cell.
        - link: The hyperlink to be inserted in the table cell.
        - text: The text content of the table cell.
        """
        with open(TESTWEBPAGE, 'a') as f:
            f.write(f'''
                    <tr>
                        <td bgcolor="{color}">{link}{text}</td>
                    </tr>
                    ''')
            
    def check_diff(self, TESTWEBPAGE, diff_path, diff_file, ref_file, test_file, file_type):
        """
        Function to compare differences between reference and test files and update a test webpage accordingly.

        This function compares the content of a reference file with a test file using the 'diff' command.
        If differences are found, it adds an entry to the test webpage indicating the difference.
        If no differences are found, it adds an entry to the test webpage indicating the test passed.

        Arguments:
        - TESTWEBPAGE: The file path of the test webpage.
        - diff_path: The directory path where the diff file will be stored.
        - diff_file: The name of the diff file.
        - ref_file: The file path of the reference file.
        - test_file: The file path of the test file.
        - file_type: The type of file being compared.

        Returns:
        - 1 if differences are found between the files.
        - 0 if no differences are found between the files.
        """
        diff_command = f"diff {ref_file} {test_file}"
        diff_output = os.popen(diff_command).read()

        if diff_output:
            self.add_entry(TESTWEBPAGE, "#FF0000", f"<a href='{diff_file}'>", file_type)
            print(f"{file_type}:")
            print(diff_output)
            with open(f"{diff_file}", "w") as df:
                df.write(diff_output)
            os.system(f"mv {diff_file} {diff_path}")
            return 1 #Exit with a diff found
        elif not os.path.isfile(f"{ref_file}"):
            self.add_entry(TESTWEBPAGE, "#FF00FF", "", f"Reference {file_type} not found")
        else:
            self.add_entry(TESTWEBPAGE, "#00FF00", "", f"{file_type} pass")
        return 0 #Exit with no diff found