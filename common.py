#####IMPORTS######
import os
import time
import json
import logging
import subprocess

class CommonWebPageFuncs:
    def __init__(self):

        #Set up logging. A more useful print that allows us to define errors, warnings, normal messages and what level these printouts happen.
        #i.e. Since this script is used as an import to the run scripts, the logger will report that the error happened in Common.
        self.logger = logging.getLogger(__name__) #default formatting is fine.
        self.logger.setLevel(logging.INFO)
        #For some strange reason, this is needed to set the right output level:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)

        try:
            # Check required environment variables
            self.ValidationPath = os.getenv("ValidationPath")
            if not self.ValidationPath:
                raise ValueError("ValidationPath environment variable is not set")

            # Load config file
            config_file_path = f"{self.ValidationPath}/git_setup.json"
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError(f"Config file not found: {config_file_path}")

            with open(config_file_path) as config_file: 
                data = json.load(config_file)

            # Check for required fields in the config file
            required_fields = ["Commit", "Validation", "Software"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field '{field}' in config file")

            # Assign config values
            self.GIT_USER = data["Commit"].get("Username", "")
            self.GIT_EMAIL = data["Commit"].get("Email", "")
            self.WEBPAGE_BRANCH = data["Validation"].get("WebPageBranch", "")
            self.WEBPAGE_FOLDER = data["Validation"].get("WebPageFolder", "")
            self.VALIDATION_GIT_PATH = data["Validation"].get("Path", "")
            self.VALIDATION_GIT_BRANCH = data["Validation"].get("CodeBranch", "")
            self.SOFTWARE_NAME = data["Software"].get("Name", "")
            self.SOFTWARE_GIT_CLONE_PATH = data["Software"].get("ClonePath", "")
            self.SOFTWARE_GIT_WEB_PATH = data["Software"].get("WebPath", "")
            self.MAX_PUSH_ATTEMPTS = 5

            # Handle optional environment variables
            self.GIT_PULL_REQUEST = os.getenv("GIT_PULL_REQUEST", "false")
            self.GIT_PULL_REQUEST_TITLE = os.getenv("GIT_PULL_REQUEST_TITLE", "")
            self.GIT_PULL_REQUEST_LINK = os.getenv("GIT_PULL_REQUEST_LINK", "")
            self.GIT_COMMIT = os.getenv("GIT_COMMIT", "")
            self.GIT_TOKEN = os.getenv("GitHubToken", "")

        except FileNotFoundError as e:
            self.logger.error(f"Config file not found: {e}")
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error in configuration: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in class CommonWebPageFuncs initialization: {e}")
    
    def run_command(self,command):
        """
        Function that runs a shell command using subprocess and catches a non-zero exit status from the command.

        Arguments:
        - command: String of the command to be run.
        """
        try:
            exit_status = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return exit_status

        except subprocess.CalledProcessError as e:
            print(f"Unexpected error in common: Command '{e.cmd}' returned non-zero exit status {e.returncode}")

    def create_directory(self,directory):
        """
        Function that creates a directory.

        Arguments:
        - directory: The absolute path of the directory to be created
        """
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as e:
            print(f"Unexpected error in common: Failed to create directory '{directory}': {e}")
    
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
        try:
            os.chdir(self.ValidationPath)

            webpage_path = os.path.join(self.ValidationPath, "Webpage")
            if not os.path.isdir(webpage_path):
                self.run_command(f"git clone https://{self.VALIDATION_GIT_PATH} --depth 1 -b {self.WEBPAGE_BRANCH} --single-branch {self.WEBPAGE_FOLDER}")
                os.chdir("Webpage")

                # Add a default user, otherwise git complains
                self.run_command(f"git config user.name {self.GIT_USER}")
                self.run_command(f"git config user.email {self.GIT_EMAIL}")

                os.chdir(f"{self.ValidationPath}")

            self.GIT_PULL_REQUEST = str(self.GIT_PULL_REQUEST) if self.GIT_PULL_REQUEST is not None else "false"
            self.logger.info("Showing GIT commit")
            self.logger.info(self.GIT_COMMIT)
            self.logger.info("Showing GIT pull request")
            self.logger.info(self.GIT_PULL_REQUEST)

        except Exception as e:
            self.logger.error(f"Unexpected error occured in checkout_validation_webpage_branch in common functions: {e}")

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
        try:
            os.chdir(os.path.join(self.ValidationPath, "Webpage"))

            # Clean up old folders
            folder = 0
            folderlist_filename = os.path.join(self.ValidationPath, "Webpage", "folderlist")
            new_folderlist_filename = folderlist_filename + '_new'
            with open(folderlist_filename, 'r') as folderlist_file:
                with open(new_folderlist_filename, 'w') as new_folderlist_file:
                    for line in folderlist_file:
                        folder += 1
                        if folder >= 35:
                            self.run_command(f"git rm -r {line.strip()}")
                        else:
                            new_folderlist_file.write(line)
            os.rename(new_folderlist_filename,folderlist_filename)

            # Setup the commit
            self.logger.info("Adding")
            self.run_command("git add --all")
            self.run_command(f"git commit -a -m CI update: new pages for {self.GIT_COMMIT}")

            # Setup a loop to prevent clashes when multiple jobs change the webpage at the same time
            for iattempt in range(self.MAX_PUSH_ATTEMPTS):
                # Get the latest version of the webpage
                self.run_command("git pull --rebase")

                # Attempt to push
                push_command = f"git push https://{self.GIT_USER}:{self.GIT_TOKEN}@{self.VALIDATION_GIT_PATH} {self.WEBPAGE_BRANCH}"
                print(push_command)
                push_process = self.run_command(push_command)

                if push_process.returncode == 0:
                    break

                #If have just finished the last push attempt and not successfully pushed...
                if iattempt == self.MAX_PUSH_ATTEMPTS - 1:
                    raise RuntimeError(f"Failed to push changes to remote repository after {self.MAX_PUSH_ATTEMPTS} attempts")

                # Have a rest before trying again
                time.sleep(15)

        except Exception as e:
            self.logger.error(f"Unexpected error occured in update_webpage in common functions: {e}")


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
        try:
            with open(TESTWEBPAGE, 'a') as f:
                f.write(f'''
                        <tr>
                            <td bgcolor="{color}">{link}{text}</td>
                        </tr>
                        ''')
        except Exception as e:
            self.logger.error(f"An unexpected error has occured in add_entry in common functions: {e}")
            
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

        Comment:
        - The exit with diff found I have kept as a return rather than within the error handling.
        - I think this make sense as if a diff is found it is not strictly an error in the validation code.
        """
        try:
            diffEntryAdded = False
            #Check if the reference file and test file exist
            if not os.path.isfile(f"{ref_file}"):
                self.add_entry(TESTWEBPAGE, "#FF00FF", "", f"Reference {file_type} not found")
                diffEntryAdded = True
                return 1
            if not os.path.isfile(f"{test_file}"):
                self.add_entry(TESTWEBPAGE, "#FF00FF", "", f"Reference {file_type} not found")
                diffEntryAdded = True
                return 1


            diff_command = f"diff {ref_file} {test_file}"
            print(ref_file)
            print(test_file)
            diff_output = os.popen(diff_command).read()

            if diff_output:
                self.add_entry(TESTWEBPAGE, "#FF0000", f"<a href='{diff_file}'>", file_type)
                diffEntryAdded = True
                self.logger.info(f"{file_type}:")
                self.logger.info(diff_output)
                with open(f"{diff_file}", "w") as df:
                    df.write(diff_output)
                os.rename(diff_file,f"{diff_path}{diff_file}") #Horrible concatenation of strings to make it work
                return 1 #Exit with a diff found
            else:
                self.add_entry(TESTWEBPAGE, "#00FF00", "", f"{file_type} pass")
                diffEntryAdded = True

            return 0 #Exit with no diff found
        
        except Exception as e:
            self.logger.error(f"An unexpected error has occured during check_diff in common functions: {e}")
            if diffEntryAdded == False:
                self.add_entry(TESTWEBPAGE, "#FF0000", f"An unexpected error has occured during check_diff in common functions: {e}")
            return 1
