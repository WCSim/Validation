#!/usr/bin/python3

import os
import json
from common import CommonWebPageFuncs

#Putting some things in functions so that the main code doesn't look a mess :)
def update_file(old_path, new_path, content):
    with open(new_path, "w") as f_new:
        f_new.write(content)
        with open(old_path, "r") as f:
            f_new.write(f.read())
    os.rename(new_path, old_path)

def build_webpage(header_path, body_path, footer_path, index_path):
    with open(index_path, "w") as f_index:
        with open(header_path, "r") as f_header:
            f_index.write(f_header.read())
        with open(body_path, "r") as f_body:
            f_index.write(f_body.read())
        with open(footer_path, "r") as f_footer:
            f_index.write(f_footer.read())

def create_commit_webpage(commit_dir, commit_body_content, run_header_path, run_footer_path):
    os.makedirs(commit_dir, exist_ok=True)
    commit_body_path = os.path.join(commit_dir, "body.html")
    with open(commit_body_path, "w") as f_body:
        f_body.write(commit_body_content)
    with open(os.path.join(commit_dir, "index.html"), "w") as f_index:
        with open(run_header_path, "r") as f_header:
            f_index.write(f_header.read())
        with open(commit_body_path, "r") as f_body:
            f_index.write(f_body.read())
        with open(run_footer_path, "r") as f_footer:
            f_index.write(f_footer.read())

def main():
    try:
        # Initialize CommonWebPageFuncs
        cw = CommonWebPageFuncs()
        logger = cw.logger

        # Checkout the validation webpage branch
        cw.checkout_validation_webpage_branch()

        # Define file paths - looks nicer this way, in my opinion.
        validation_path = cw.ValidationPath
        folderlist_path = os.path.join(validation_path, "Webpage", "folderlist")
        body_path = os.path.join(validation_path, "Webpage", "body.html")
        header_path = os.path.join(validation_path, "Webpage", "templates", "main", "header.html")
        footer_path = os.path.join(validation_path, "Webpage", "templates", "main", "footer.html")
        run_header_path = os.path.join(validation_path, "Webpage", "templates", "run", "header.html")
        run_footer_path = os.path.join(validation_path, "Webpage", "templates", "run", "footer.html")

        # Check file existence
        paths_to_check = [
            folderlist_path,
            body_path,
            header_path,
            footer_path,
            run_header_path,
            run_footer_path
        ]
        for file_path in paths_to_check:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"The file '{file_path}' does not exist")

        # Update folderlist
        new_folderlist_path = f"{folderlist_path}.new"
        update_file(folderlist_path, new_folderlist_path, f"{cw.GIT_COMMIT} \n")

        # Update body
        git_commit_message = f" Pull Request #{cw.GIT_PULL_REQUEST}: {cw.GIT_PULL_REQUEST_TITLE}" if cw.GIT_PULL_REQUEST != "false" else ""
        git_pull_request_link = f"<a href=https://github.com/WCSim/WCSim/pull/{cw.GIT_PULL_REQUEST}>"
        git_pull_request_link_close = "</a>" if not cw.GIT_PULL_REQUEST.isdigit() else ""
        new_body_path = f"{body_path}.new"
        update_file(body_path, new_body_path, f"\n<tr> <td><a href='{cw.GIT_COMMIT}/index.html'>{cw.GIT_COMMIT}</td> <td>{git_pull_request_link}{git_commit_message}{git_pull_request_link_close}</td> </tr>\n")

        # Build webpage
        build_webpage(header_path, body_path, footer_path, os.path.join(validation_path, "Webpage", "index.html"))

        # Make the test webpage
        commit_dir = os.path.join(validation_path, "Webpage", cw.GIT_COMMIT)
        commit_body_content = "<h2>{cw.GIT_COMMIT}</h2>\n" + \
                            f"<h3>{git_pull_request_link}{git_commit_message}{git_pull_request_link_close}</h3>\n" + \
                            "<p>\n<table  border='1' align='center'>\n <tr>\n  <th scope='col'><div align='center'>Test num</div></th>\n  <th scope='col'><div align='center'>Physics test</div></th>\n </tr>\n"
        
        with open(os.path.join(validation_path,'tests.json'), 'r') as json_file:
            data = json.load(json_file)
            for key, value in data.items():
                itest = key[len("Test"):]
                if key.startswith("Test") and itest.isdigit():
                    name = value["name"]
                    itestpad = f"{int(itest):04d}"
                    commit_body_content += f"  <tr>\n    <td>{itest}</td>\n    <td bgcolor='#00FFFF'COLOUR{itestpad}><a href='{itest}/index.html'>{name}</td>\n  </tr>\n"
            commit_body_content += "</table>\n"

        create_commit_webpage(commit_dir, commit_body_content, run_header_path, run_footer_path)

        # Update webpage
        cw.update_webpage()

    except FileNotFoundError as e:
        logger.error(f"An unexpected FileNotFoundError has occurred in SetupWebpages: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in SetupWebpages: {e}")

if __name__ == "__main__":
    main()
