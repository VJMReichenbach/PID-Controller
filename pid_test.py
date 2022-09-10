#!/usr/bin/python3

from simple_pid import PID
import argparse

ver = "0.0.1"
author = "Valentin Reichenbach"
description = f"""
TODO: Insert description
"""
epilog = f"""
Author: {author}
Version: {ver}
License: GPLv3+
"""

def debugMode():
    print('TODOOOO')

def normalMode():
    print('TODOO: EPICS interface not yet implemented')
    exit()

def main():
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--debug', action='store_true', default=False, help="uses a test enviroment instead of the epics interface")
    parser.add_argument('--version', action='version', version=ver)


    args = parser.parse_args()

    if args.debug == True:
        debugMode()
    else:
        normalMode()

    
if __name__ == '__main__':
    main()