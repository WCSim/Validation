#!/usr/bin/python3

import os
import argparse
from common import CommonWebPageFuncs

def main(args):

    cw = CommonWebPageFuncs()
    extra_options = ""

    if args.overlap_check:
        extra_options = "-DWCSim_Geometry_Overlaps_CHECK=ON -DWCSim_Geometry_PMT_Overlaps_CHECK=ON"

    cw.create_directory("build")
    cw.create_directory("install")
    os.chdir("build")

    cmake_command = f"cmake -DWCSim_DEBUG_COMPILE_FLAG=ON {extra_options} -DCMAKE_INSTALL_PREFIX=../install/ ../src/"
    make_command = "make"
    if args.parallel:
        make_command += " -j`nproc`" 
    make_install_command = "make install"

    cw.run_command(cmake_command)
    cw.run_command(make_command)
    cw.run_command(make_install_command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and install script")
    parser.add_argument("--parallel", action='store_true', help="Build code in parallel?")
    parser.add_argument("--overlap-check", action='store_true', help="Build with overlap checking on? WARNING! Running with this is very slow!")
    args = parser.parse_args()
    main(args)
