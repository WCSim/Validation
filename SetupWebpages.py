#####IMPORTS#####
import os
import json
from common import CommonWebPageFuncs

#Initialise the common object (cw) which in turn initialises all relevant environment variables.
cw = CommonWebPageFuncs()


#Checkout the validation webpage branch - common function, should add as such.
cw.checkout_validation_webpage_branch()


# Do some specific things here. Can this be made into a common function? No way of testing...
if cw.GIT_PULL_REQUEST != "false":
        git_commit_message = f" Pull Request #{cw.GIT_PULL_REQUEST}: {cw.GIT_PULL_REQUEST_TITLE}"
else:
        git_commit_message = ""

# First update the list of commits
with open(f"{cw.ValidationPath}/Webpage/folderlist.new", "w") as f_new:
    f_new.write(f"{cw.GIT_COMMIT} \n")
    with open(f"{cw.ValidationPath}/Webpage/folderlist", "r") as f:
        f_new.write(f.read())
os.rename(f"{cw.ValidationPath}/Webpage/folderlist.new", f"{cw.ValidationPath}/Webpage/folderlist")

# Update the main page.
try:
    if int(cw.GIT_PULL_REQUEST) >= 0:
        git_pull_request_link = f"<a href=https://github.com/WCSim/WCSim/pull/{cw.GIT_PULL_REQUEST}>"
        git_pull_request_link_close = "</a>"
except ValueError:
    git_pull_request_link = ""
    git_pull_request_link_close = ""

with open(f"{cw.ValidationPath}/Webpage/body.html.new", "w") as f_new:
    f_new.write(f"\n<tr> <td><a href='{cw.GIT_COMMIT}/index.html'>{cw.GIT_COMMIT}</td> <td>{git_pull_request_link}{git_commit_message}{git_pull_request_link_close}</td> </tr>\n")
    with open(f"{cw.ValidationPath}/Webpage/body.html", "r") as f:
        f_new.write(f.read())
os.rename(f"{cw.ValidationPath}/Webpage/body.html.new", f"{cw.ValidationPath}/Webpage/body.html")

# Build the webpage
with open(f"{cw.ValidationPath}/Webpage/index.html", "w") as f_index:
    with open(f"{cw.ValidationPath}/Webpage/templates/main/header.html", "r") as f_header:
        f_index.write(f_header.read())
    with open(f"{cw.ValidationPath}/Webpage/body.html", "r") as f_body:
        f_index.write(f_body.read())
    with open(f"{cw.ValidationPath}/Webpage/templates/main/footer.html", "r") as f_footer:
        f_index.write(f_footer.read())

# Make the test webpage
commit_dir = os.path.join(cw.ValidationPath, "Webpage", cw.GIT_COMMIT)
os.makedirs(commit_dir, exist_ok=True)

with open(os.path.join(commit_dir, "body.html"), "w") as f_body:
    f_body.write(f"<h2>{cw.GIT_COMMIT}</h2>\n")
    f_body.write(f"<h3>{git_pull_request_link}{git_commit_message}{git_pull_request_link_close}</h3>\n")
    f_body.write("<p>\n<table  border='1' align='center'>\n <tr>\n  <th scope='col'><div align='center'>Test num</div></th>\n  <th scope='col'><div align='center'>Physics test</div></th>\n </tr>\n")

    # Load in tests.json
    with open(os.path.join(cw.ValidationPath,'tests.json'), 'r') as json_file:
        data = json.load(json_file)
        # Loop over relevant tests i.e. those with numbers and not letters.
        for key, value in data.items():
            # Check if test is relevant.
            itest = key[len("Test"):]
            if key.startswith("Test") and itest.isdigit(): #Make sure last character is a digit.
                name = value["name"]
                itestpad = f"{int(itest):04d}"
                f_body.write(f"  <tr>\n    <td>{itest}</td>\n    <td bgcolor='#00FFFF'COLOUR{itestpad}><a href='{itest}/index.html'>{name}</td>\n  </tr>\n")

    f_body.write("</table>\n")

# Is there a better way to do this? 
with open(os.path.join(commit_dir, "index.html"), "w") as f_index:
    with open(f"{cw.ValidationPath}/Webpage/templates/run/header.html", "r") as f_header:
        f_index.write(f_header.read())
    with open(os.path.join(commit_dir, "body.html"), "r") as f_body:
        f_index.write(f_body.read())
    with open(f"{cw.ValidationPath}/Webpage/templates/run/footer.html", "r") as f_footer:
        f_index.write(f_footer.read())


#############################################################

############################## update webpage ################
cw.update_webpage() 
