#####IMPORTS#####
import os
import WebpageFunctions
import json

# Grab environment variables - wildly inconsistent variable naming. Will fix at some point.
ValidationPath = os.getenv("ValidationPath")
TRAVIS_PULL_REQUEST = os.getenv("TRAVIS_PULL_REQUEST","false")
TRAVIS_PULL_REQUEST_TITLE = os.getenv("TRAVIS_PULL_REQUEST_TITLE","")
TRAVIS_PULL_REQUEST_LINK = os.getenv("TRAVIS_PULL_REQUEST_LINK","")
TRAVIS_COMMIT = os.getenv("TRAVIS_COMMIT","")
GITHUBTOKEN = os.getenv("GITHUBTOKEN","")


#Checkout the validation webpage branch - common function, should add as such.
WebpageFunctions.checkout_validation_webpage_branch(ValidationPath,TRAVIS_PULL_REQUEST,TRAVIS_COMMIT)


# Do some specific things here. Can this be made into a common function? No way of testing...
if os.environ.get("TRAVIS_PULL_REQUEST") != "false":
        travis_commit_message = f" Pull Request #{os.environ.get('TRAVIS_PULL_REQUEST')}: {os.environ.get('TRAVIS_PULL_REQUEST_TITLE')}"

# First update the list of commits
with open(f"{ValidationPath}/Webpage/folderlist.new", "w") as f_new:
    f_new.write(os.environ.get("TRAVIS_COMMIT") + "\n")
    with open(f"{ValidationPath}/Webpage/folderlist", "r") as f:
        f_new.write(f.read())
os.rename(f"{ValidationPath}/Webpage/folderlist.new", f"{ValidationPath}/Webpage/folderlist")

# Update the main page
if int(os.environ.get("TRAVIS_PULL_REQUEST")) >= 0:
    travis_pull_request_link = f"<a href=https://github.com/WCSim/WCSim/pull/{os.environ.get('TRAVIS_PULL_REQUEST')}>"
    travis_pull_request_link_close = "</a>"

with open(f"{ValidationPath}/Webpage/body.html.new", "w") as f_new:
    f_new.write(f"\n<tr> <td><a href='{os.environ.get('TRAVIS_COMMIT')}/index.html'>{os.environ.get('TRAVIS_COMMIT')}</td> <td>{travis_pull_request_link}{travis_commit_message}{travis_pull_request_link_close}</td> </tr>\n")
    with open(f"{ValidationPath}/Webpage/body.html", "r") as f:
        f_new.write(f.read())
os.rename(f"{ValidationPath}/Webpage/body.html.new", f"{ValidationPath}/Webpage/body.html")

# Build the webpage
with open(f"{ValidationPath}/Webpage/index.html", "w") as f_index:
    with open(f"{ValidationPath}/Webpage/templates/main/header.html", "r") as f_header:
        f_index.write(f_header.read())
    with open(f"{ValidationPath}/Webpage/body.html", "r") as f_body:
        f_index.write(f_body.read())
    with open(f"{ValidationPath}/Webpage/templates/main/footer.html", "r") as f_footer:
        f_index.write(f_footer.read())

# Make the test webpage
commit_dir = os.path.join(ValidationPath, "Webpage", os.environ.get("TRAVIS_COMMIT"))
os.makedirs(commit_dir, exist_ok=True)

with open(os.path.join(commit_dir, "body.html"), "w") as f_body:
    f_body.write(f"<h2>{os.environ.get('TRAVIS_COMMIT')}</h2>\n")
    f_body.write(f"<h3>{travis_pull_request_link}{travis_commit_message}{travis_pull_request_link_close}</h3>\n")
    f_body.write("<p>\n<table  border='1' align='center'>\n <tr>\n  <th scope='col'><div align='center'>Test num</div></th>\n  <th scope='col'><div align='center'>Physics test</div></th>\n </tr>\n")

    # Load in tests.json
    with open(os.path.join(ValidationPath,'tests.json'), 'r') as json_file:
        data = json.load(json_file)
        # Loop over relevant tests i.e. those with numbers and not letters.
        for key, value in data.items():
            # Check if test is relevant.
            itest = key[len("Test"):]
            if key.startswith("Test") and itest.isdigit(): #Make sure last character is a digit.
                name = value["name"]
                itestpad = f"{itest:04d}"
                f_body.write(f"  <tr>\n    <td>{itest}</td>\n    <td bgcolor='#00FFFF'COLOUR{itestpad}><a href='{itest}/index.html'>{name}</td>\n  </tr>\n")

    f_body.write("</table>\n")

# Is there a better way to do this? 
with open(os.path.join(commit_dir, "index.html"), "w") as f_index:
    with open(f"{ValidationPath}/Webpage/templates/run/header.html", "r") as f_header:
        f_index.write(f_header.read())
    with open(os.path.join(commit_dir, "body.html"), "r") as f_body:
        f_index.write(f_body.read())
    with open(f"{ValidationPath}/Webpage/templates/run/footer.html", "r") as f_footer:
        f_index.write(f_footer.read())


#############################################################

############################## update webpage ################

WebpageFunctions.update_webpage(ValidationPath,TRAVIS_COMMIT,GITHUBTOKEN) 