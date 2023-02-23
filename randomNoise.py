#!/usr/bin/python3
import argparse
from os import remove
from pathlib import Path
import time
import numpy as np
from epics import caput, caget
import subprocess

ver = "1.4.0"
author = "Valentin Reichenbach"
description = """
This program is used to generate noise for a PV in an epics system.
In normal mode it will apply the noise to a given PV.
In debug mode it will continuously write to a given text file to simulate a debug enviroment.
"""
epilog = """
Author: Valentin Reichenbach
Version: 1.4.0
License: GPLv3+
"""

def writeToDebugFile(debugFile: str, content, args):
    content = str(content)

    f = open(debugFile, 'w')
    f.write(content)
    if args.verbose >= 1:
        print('Written '+ content + ' to ' + str(debugFile) + '')
    f.close()

def getFromDebugFile(debugFile: str, lastVal: float, args) -> float:
    f = open(debugFile, 'r')
    content = f.read()
    f.close()

    try:
        float(content)
    except Exception as e:
        if args.verbose >= 1:
            print('Error while reading ' + str(debugFile) + '!')
            print('Exception: ', e)
        content = lastVal

    return content

def readSinFile(verbose: int):
    f = open('sin.txt', 'r')
    content = f.read()
    f.close()
    if verbose >= 3:
        print('sin.txt: ' + str(content))
    return content

def generateNoise(i, y, count, no_delete: bool, file: str, noise_type: str, noise_strength: float, drift: float, period: float, fileVal: float, verbose: int) -> float:
    time_start = time.time()
    if noise_type == 'normal':
        # draws a random value from normal (Gaussian) distribution bewteen -1 and 1
        noise = noise_strength * np.random.normal(0,1,1)[0] + drift
        noise = float(noise) + float(fileVal)
    elif noise_type == 'sin':
        if i == 0:
            lastSin = y[count-1]
        else:
            lastSin = y[i-1]
        diff = y[i] - lastSin
        i = i + 1
        if i >= count:
            i = 0
        # sleep 
        while time.time() - time_start < period/count:
            pass
        noise = diff + fileVal
    elif noise_type == 'mix':
        # draws a random value from a mixture of a normal distribution and a sine wave bewteen -1 and 1
        # by calling the normal and sin functions
        normal_noise , _ = generateNoise(i, y, count, no_delete=no_delete, file=file, noise_type='normal', noise_strength=noise_strength, drift=drift, period=period, fileVal=fileVal, verbose=verbose)
        sin_noise , i = generateNoise(i, y, count, no_delete=no_delete, file=file, noise_type='sin', noise_strength=noise_strength, drift=drift, period=period, fileVal=fileVal, verbose=verbose)
        noise = (normal_noise + sin_noise) / 2
        noise = noise 
    else:
        print('Error: noise type ' + noise_type + ' not recognized')
        return 0
    return noise , i

def debugMode(args):
    # check if debug file already exists
    try:
        remove("debugEnv.txt")
    except:
        pass

    print('Starting...')

    # create the debug file
    debugFile = Path(args.file)
    # convert to str for python 3.5
    debugFile = str(debugFile)
    writeToDebugFile(debugFile=debugFile, content=1, args=args)

    # set the last value to the niveau
    lastVal= 1.0
    i = 0

    count = 100
    x = 2 * np.pi * np.arange(count) / count
    y = args.amplitude * np.sin(x) + args.shift

    try:
        while True:
            # Writes a random value to the debugfile
            fileVal = getFromDebugFile(debugFile=debugFile, lastVal=lastVal, args=args)
            fileVal = float(fileVal)
            noise , i = generateNoise(i, y, count, no_delete=args.no_delete, file=args.file, noise_type=args.noise_type, noise_strength=args.noise_strength, drift=args.drift, period=args.period, fileVal=fileVal, verbose=args.verbose)

            # if the noise gets read incorrectly, use the last value
            if noise == '':
                if args.verbose >= 2:
                    print('Error while reading noise. Using 0')
                noise = 0

            # conversion to float because python threw an error otherwise
            if args.verbose >= 3:
                print('fileVal: ' + str(fileVal))
                print('noise: ' + str(noise))
                print('lastVal: ' + str(lastVal))

            # write the new value to the debug file
            writeToDebugFile(debugFile=debugFile, content=noise, args=args)
            if args.verbose >= 3:
                print('')

            # update the last value
            lastVal = noise

            # wait for the next iteration
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        return 


def normalMode(args):
    print('Starting in Normal Mode...')

    # get first value
    lastVal= caget(args.pv + ":outCur")
    i = 0

    count = 100
    x = 2 * np.pi * np.arange(count) / count
    y = args.amplitude * np.sin(x) + args.shift

    try:
        while True:
            # get value from other script
            currentVal = caget(args.pv + ":outCur")

            noise , i = generateNoise(i, y, count, False, "debugEnv.txt", noise_type=args.noise_type, noise_strength=args.noise_strength, drift=args.drift, period=args.period, fileVal=lastVal, verbose=args.verbose)

            # if the noise gets read incorrectly, use the last value
            if noise == '':
                if args.verbose >= 2:
                    print('Error while reading noise. Using 0')
                noise = 0

            # conversion to float because python threw an error otherwise
            if args.verbose >= 3:
                print('fileVal: ' + str(fileVal))
                print('noise: ' + str(noise))
                print('lastVal: ' + str(lastVal))

            # write new value to pv
            newVal = currentVal + noise
            caput(args.pv + ":outCur", newVal)

            # update the last value
            lastVal = noise

            # wait for the next iteration
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        return 

def cleanup(no_delete: bool, file: str, noise_type: str, mode: str):
    if no_delete == False and mode == 'debug':
        try:
            remove(file)
        except Exception as e:
            print('Something went wrong while deleting ' + str(file) + '!')
            print(e)
    if noise_type == 'sin':
        try:
            # kill subprocess
            subprocess.run(['pkill', '-f', 'sinenoise.py'])
        except Exception as e:
            print('Something went wrong while killing the sinenoise subprocess!')
            print(e)

        try:
            # delete sin.txt
            remove('sin.txt')
        except Exception as e:
            print('Something went wrong while deleting sin.txt!')
            print(e)


def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parentParser = argparse.ArgumentParser('The parent parser', add_help=False)

    # general options
    parentParser.add_argument('-d','--delay', type=float, default=0.05, help='delay between each write in miliseconds. The default value is 0.05')
    parentParser.add_argument('-v', '--verbose', action='count', default=0, help='verbose output')
    parentParser.add_argument('--version', action='version', version=ver)
    parentParser.add_argument('--noise-strength', type=float, default=0.5, help='the strength of the noise. The default value is 0.5')
    parentParser.add_argument('--drift', type=float, default=0.0, help='the drift of the noise. The default value is 0.0')
    parentParser.add_argument('--noise-type', type=str, default='normal', help='the type of noise that should be generated. The default value is "normal" (a normal distribution). Alternativly, you can use "sin" for noise a sine wave like noise, or "mix for a bixture of both"')
    parentParser.add_argument("--period", type=float, default=10, help="the period of the sine wave in seconds. The default value is 10")
    parentParser.add_argument('--shift', type=float, default=0.0, help='the shift of the sine wave. The default value is 0.0')
    parentParser.add_argument('--amplitude', type=float, default=1.0, help='the amplitude of the sine wave. The default value is 1.0')

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
    try:
        args.file = str(args.file)
    except:
        pass

    # # start sine noise script with the given arguments if asked for
    # if args.noise_type == 'sin' or args.noise_type == 'mix':
    #     cmd = ['python3', 'sinenoise.py', "--force"]
    #     sleep(1)
    #     if args.frequency:
    #         cmd.append('--frequency')
    #         cmd.append(str(args.frequency))
    #     if args.verbose > 0:
    #         print('Starting sine noise script with cmd:')
    #         cmd_str = ''
    #         for i in cmd:
    #             cmd_str += i + ' '
    #         print(cmd_str)
    #     # start the sine noise script as a subprocess
    #     subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # sleep shortly to let subprocess start
    # sleep(1)

    # start the given mode    
    if args.mode == 'debug':
        debugMode(args)
    elif args.mode == 'normal':
        normalMode(args)
        # set debug mode rélated variables to default values
        # script crashes otherwise
        args.no_delete = False
        args.file = 'debugEnv.txt'
    else:
        print('Something went wrong while parsing the arguments\nExiting...')

    # cleanup
    cleanup(no_delete=args.no_delete, file=args.file, noise_type=args.noise_type, mode=args.mode)

    
if __name__ == '__main__':
    main()
