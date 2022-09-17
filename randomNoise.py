#!/usr/bin/python3
import argparse
from os import remove
from pathlib import Path
from time import sleep
import numpy as np

ver = "1.0.0"
author = "Valentin Reichenbach"
description = f"""
TODO: Insert description
"""
epilog = f"""
Author: {author}
Version: {ver}
License: GPLv3+
"""

def writeToDebugFile(debugFile: Path, content, args):
    content = str(content)

    f = open(debugFile, 'w')
    f.write(content)
    if args.verbose >= 1:
        print(f'Written {content} to {debugFile}')
    f.close()

def generateNoise(args, noiseStrength: float=0.5) -> float:
    # TODO: add other noise types (like sin)

    # draws a random value from normal (Gaussian) distribution bewteen -1 and 1
    noise = noiseStrength * np.random.normal(0,1,1)[0]
    return noise 


def debugMode(args):
    # check if debug file already exists
    try:
        remove("debugEnv.txt")
    except:
        pass

    # create the debug file
    debugFile = Path(args.file)
    writeToDebugFile(debugFile=debugFile, content=1, args=args)
    lastVal = 1

    try:
        while True:
            # Writes a random value to the debugfile
            r = lastVal + generateNoise(args=args)
            writeToDebugFile(debugFile=debugFile, content=r, args=args)
            lastVal = r
            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        #TODO: necessary cleanup?
        exit()


def normalMode(args):
    # TODO: normal mode
    print('normal mode not yet implemented\nExiting...')
    exit()

def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parentParser = argparse.ArgumentParser('The Parrent parser', add_help=False)

    # general options
    parentParser.add_argument('-d','--delay', type=float, default=0.05, help='delay between each write in miliseconds. The default value is 0.05')
    parentParser.add_argument('-v', '--verbose', action='count', default=0, help='verbose output')
    parentParser.add_argument('--version', action='version', version=ver)

    # subcommands
    subparsers = parser.add_subparsers(dest='mode', help='the program can use an epics interface or create a debug enviroment for another script')
    subparsers.required = True

    # normal mode
    pvParser = subparsers.add_parser('normal', help='uses the epics interface', parents=[parentParser])
    pvParser.add_argument('--pv', type=str, default='I1SV02' ,help='the process variable that should be controlled. The default is I1SV02')
    pvParser.add_argument('--force', action='store_true', default=False,
                        help='forces the pv connect check to pass. This is should only be used for development and testing purposes')

    # debug mode
    debugParser = subparsers.add_parser('debug', help='controls a test enviroment instead of the epics interface', parents=[parentParser])
    debugParser.add_argument('-f', '--file', type=str, default='debugEnv.txt', help='simulates a debug enviroment for a controller script using a file called "debugEnv.txt"')


    args = parser.parse_args()

    # start the given mode    
    if args.mode == 'debug':
        debugMode(args)
    elif args.mode == 'normal':
        normalMode(args)
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()

    
if __name__ == '__main__':
    main()