#!/usr/bin/python3
import argparse
from os import remove
from pathlib import Path
from queue import PriorityQueue
from time import sleep
import numpy as np
from epics import caput

ver = "1.4.0"
author = "Valentin Reichenbach"
description = f"""
This program is used to generate noise for a PV in an epics system.
In normal mode it will apply the noise to a given PV.
In debug mode it will continuously write to a given text file to simulate a debug enviroment.
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

def getFromDebugFile(debugFile: Path, lastVal: float, args) -> float:
    f = open(debugFile, 'r')
    content = f.read()
    f.close()

    try:
        float(content)
    except Exception as e:
        if args.verbose >= 1:
            print(f'Error while reading {debugFile}!\n{e}')
        content = lastVal

    return content

def generateNoise(args) -> float:
    # TODO: add other noise types (like sin)

    # draws a random value from normal (Gaussian) distribution bewteen -1 and 1
    noise = args.noise_strength * np.random.normal(0,1,1)[0] + args.drift
    return noise 


def debugMode(args):
    # check if debug file already exists
    try:
        remove("debugEnv.txt")
    except:
        pass

    print('Starting...')

    # create the debug file
    debugFile = Path(args.file)
    writeToDebugFile(debugFile=debugFile, content=1, args=args)

    # set the last value to the niveau
    lastVal:float = 1.0

    try:
        while True:
            # Writes a random value to the debugfile
            fileVal = getFromDebugFile(debugFile=debugFile, lastVal=lastVal, args=args)
            noise = generateNoise(args=args)

            # conversion to float because python threw an error otherwise
            r = float(fileVal) + float(noise)

            # write the new value to the debug file
            writeToDebugFile(debugFile=debugFile, content=r, args=args)

            # update the last value
            lastVal = r

            # wait for the next iteration
            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        # Cleanup
        if args.no_delete == False:
            try:
                remove(debugFile)
            except Exception as e:
                print(f'Something went wrong while deleting {debugFile}!\n{e}')
        exit()


def normalMode(args):
    if args.force == False:
        print('normal mode is currently not tested. Use the --force flag to force the program to run')
        print('Exiting...')
        exit()

    lastVal = 0

    try:
        while True:
            # Writes a random value to the debugfile
            r = lastVal + generateNoise(args=args)
            caput(args.pv, r)
            lastVal = r
            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        # Cleanup
        exit()

def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parentParser = argparse.ArgumentParser('The Parrent parser', add_help=False)

    # general options
    parentParser.add_argument('-d','--delay', type=float, default=0.05, help='delay between each write in miliseconds. The default value is 0.05')
    parentParser.add_argument('-v', '--verbose', action='count', default=0, help='verbose output')
    parentParser.add_argument('--version', action='version', version=ver)
    parentParser.add_argument('--noise-strength', type=float, default=0.5, help='the strength of the noise. The default value is 0.5')
    parentParser.add_argument('--drift', type=float, default=0.0, help='the drift of the noise. The default value is 0.0')

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
    debugParser.add_argument('--no-delete', action='store_true', default=False, help='doesn\'t delete the debug env file after running the program')


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