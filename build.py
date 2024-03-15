#!/usr/bin/python3

import os
import argparse

def main(option):
    extra_options = ""

    if option == 1:
        extra_options = "WCSim_Geometry_Overlaps_CHECK=ON"

    os.makedirs("build", exist_ok=True)
    os.makedirs("install", exist_ok=True)
    os.chdir("build")

    cmake_command = f"cmake -DWCSim_DEBUG_COMPILE_FLAG=ON {extra_options} -DCMAKE_INSTALL_PREFIX=../install/ ../src/"
    make_command = "make"
    make_install_command = "make install"

    os.system(cmake_command)
    os.system(make_command)
    os.system(make_install_command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and install script")
    parser.add_argument("-o","--option", required=True,type=int, help="Option to pass to the script. Option 0 does nothing. Option 1 sets WCSim_Geometry_Overlaps_CHECK=ON", choices=list(range(2)))
    args = parser.parse_args()
    main(args.option)