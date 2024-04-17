#!/usr/bin/python3

import os
import argparse
import subprocess
import sys

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Unexpected error in build: Command '{e.cmd}' returned non-zero exit status {e.returncode}")
        sys.exit(1)

def create_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        print(f"Unexpected error in build: Failed to create directory '{directory}': {e}")
        exit(1)

def main(option):
    extra_options = ""

    if option == 1:
        extra_options = "WCSim_Geometry_Overlaps_CHECK=ON"

    create_directory("build")
    create_directory("install")
    os.chdir("build")

    cmake_command = f"cmake -DWCSim_DEBUG_COMPILE_FLAG=ON {extra_options} -DCMAKE_INSTALL_PREFIX=../install/ ../src/"
    make_command = "make"
    if option == 1:
        make_command += " -j`nproc`" 
    make_install_command = "make install"

    run_command(cmake_command)
    run_command(make_command)
    run_command(make_install_command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and install script")
    parser.add_argument("-o","--option", required=True,type=int, help="Option to pass to the script. Option 0 does nothing. Option 1 sets WCSim_Geometry_Overlaps_CHECK=ON & compiles with multiple threads", choices=list(range(2)))
    args = parser.parse_args()
    main(args.option)
