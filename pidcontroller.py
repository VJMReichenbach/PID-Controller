#!/usr/bin/python3
from os import remove
from epics import caget, caput
from simple_pid import PID
import argparse
from pathlib import Path
from time import sleep, time
import matplotlib.pyplot as plt

ver = "1.1.0"
author = "Valentin Reichenbach"
description = """
TODO: Insert description
"""
epilog = """
Author: Valentin Reichenbach
Version: 1.1.0
License: GPLv3+
"""    

def getCurrentVal(args, debugFile: str) -> float:
    if args.mode == 'debug':
        # Check if the debug file exists
        try:
            f = open(debugFile, 'r')
            val = f.read()
            f.close()
        except Exception as e:
            print('The debug file ' + str(debugFile) + ' was not found')
            print('Exception: ', e)
            print('Exiting...')
            exit()
        
        # BUG: sometimes nothing is read when not in v mode
        try:
            val = float(val)
        except Exception as e:
            if args.verbose >= 1:
                print('couldn\'t convert val: "' + str(val) + '" to float. Returned 0 instead')
            if args.verbose >= 2:
                print('Exception: ', e)
            val = 0

        return val
    elif args.mode == 'normal':
        # unused
        return caget(args.pv)
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


def debugMode(args):
    debugFile = args.file
    args.pv = 'debug'
    getCurrentVal(args=args, debugFile=debugFile)

    pid = PID(Kp=args.proportional, Kd=args.derivative, Ki=args.integral, setpoint=args.niveau)

    x = []
    y1 = []
    y2 = []
    y3 = []

    plt.ion() # plot all graphs in the same window

    startTime = time()

    graphLen = 80

    # log options
    if args.log == True:
        logFile = args.log_file
        header = 'PID-Controller Log File\nPV: ' + str(args.pv) + '\nKp: ' + str(args.proportional) + '\nKi: ' + str(args.integral) + '\nKd: ' + str(args.derivative) + '\nNiveau: ' + str(args.niveau) + '\nDelay: ' + str(args.delay) + '\n\n'
        with open(logFile, 'w') as l:
            l.write(header)
            l.write('time, corrected Value, current Value\n')
            l.close()

    try:
        while True:
            currentVal = getCurrentVal(args=args, debugFile=debugFile)
            fileVal = currentVal

            # get new value
            correctVal = float(pid(currentVal)) + currentVal

            # wrtie new value to debug file
            f = open(debugFile, 'w')
            f.write(str(correctVal))
            f.close()

            if args.verbose >= 2:
                print('time: ' + str(time()-startTime) + ', corrected Value: ' + str(correctVal) + ', current Value: ' + str(currentVal) + '')

            if args.log == True:
                logFile = args.log_file
                l = open(logFile, 'a')
                l.write(str(time() - startTime) + ', ' + str(correctVal) + ', ' + str(currentVal) + '\n')
                l.close()
            
            
            # plotting
            if args.visualize == True:

                x.append(time() - startTime)
                y1.append(correctVal)
                y2.append(args.niveau)
                y3.append(fileVal)

                # makes sure that the graph doesnt grow infinitly
                if len(x) >= graphLen:
                    x.pop(0)
                if len(y1) >= graphLen:
                    y1.pop(0)
                if len(y2) >= graphLen:
                    y2.pop(0)
                if len(y3) >= graphLen:
                    y3.pop(0)

                plt.cla() # clear axes

                plt.title('correct: ' + str(correctVal))
                plt.plot(x, y1, label='Value')
                plt.plot(x, y2, label='Niveau')
                plt.plot(x, y3, label='Current Value')
                plt.legend(loc='upper left')

                plt.pause(0.1)

            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        exit()

def deltaI(deltaX):
    return -0.021836 * deltaX



def normalMode(args):
    currentVal = caget(args.pv + ':outCur')

    pid = PID(Kp=args.proportional, Kd=args.derivative, Ki=args.integral, setpoint=args.niveau)

    x = []
    y1 = []
    y2 = []
    y3 = []

    plt.ion() # plot all graphs in the same window

    startTime = time()

    graphLen = 80

    # log options
    if args.log == True:
        logFile = args.log_file
        header = 'PID-Controller Log File\nPV: ' + str(args.pv) + '\nKp: ' + str(args.proportional) + '\nKi: ' + str(args.integral) + '\nKd: ' + str(args.derivative) + '\nNiveau: ' + str(args.niveau) + '\nDelay: ' + str(args.delay) + '\n\n'
        with open(logFile, 'w') as l:
            l.write(header)
            l.write('time, current pos, corrected pos, current shift, current current, new current')
            l.close()

    try:
        while True:
            f = open('position.txt', 'r')
            current_pos = float(f.read())
            f.close()

            # get new value
            corrected_pos = float(pid(current_pos)) + current_pos

            pos_shift = corrected_pos - current_pos

            current_shift = deltaI(pos_shift)

            # write new value to pv
            current_current = caget(args.pv + ':outCur')
            new_current = current_current - current_shift
            caput(args.pv + ':outCur', new_current)
            

            if args.verbose >= 2:
                print('time: ' + str(time()-startTime) + ', current_pos: ' + str(current_pos) + ', corrected_pos: ' + str(corrected_pos) + ', current_shift: ' + str(current_shift) + ', current_current: ' + str(current_current) + ', new_current: ' + str(new_current) + '')

            if args.log == True:
                logFile = args.log_file
                l = open(logFile, 'a')
                l.write(str(time() - startTime) + ', ' + str(current_pos) + ', ' + str(corrected_pos) + ', ' + str(current_shift) + ', ' + str(current_current) + ', ' + str(new_current) + '\n')
                l.close()
            
            
            # plotting
            if args.visualize == True:

                x.append(time() - startTime)
                y1.append(current_pos)
                y2.append(args.niveau)

                # makes sure that the graph doesnt grow infinitly
                if len(x) >= graphLen:
                    x.pop(0)
                if len(y1) >= graphLen:
                    y1.pop(0)
                if len(y2) >= graphLen:
                    y2.pop(0)
                if len(y3) >= graphLen:
                    y3.pop(0)

                plt.cla() # clear axes

                plt.title('correct: ' + str(correctVal))
                plt.plot(x, y1, label='Current Position')
                plt.plot(x, y2, label='Niveau')
                plt.legend(loc='upper left')

                plt.pause(0.1)

            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        exit()

def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter) 
    
    parentParser = argparse.ArgumentParser('The Parrent parser', add_help=False)
    
    # general options
    parentParser.add_argument('--visualize', action='store_true', default=False, help='visualize the changed values live')
    parentParser.add_argument('--version', action='version', version=ver)
    parentParser.add_argument('-v', '--verbose', action='count', default=0, help='verbose output')
    parentParser.add_argument('--force', action='store_true', default=False,
                              help='forces all checks like the pv connect chec to pass. Additionally every file used (like "log.txt") will be overwritten This is should only be used for development and testing purposes')

    # PID controller options
    pidControllerOptions = parentParser.add_argument_group('PID-Controller options')
    pidControllerOptions.add_argument('-p', '--proportional', type=float, default=0.5,
                        help='specifys the coefficient for the proportional term')
    pidControllerOptions.add_argument('-i', '--integral', type=float, default=0.3,
                        help='specifys the coefficient for the integral term')
    pidControllerOptions.add_argument('-d', '--derivative', type=float, default=0,
                        help='specifys the coefficient for the derivative term')
    pidControllerOptions.add_argument('-n', '--niveau', type=float, default=1,
                        help='specifys the niveau that the PID controler should aim for')
    pidControllerOptions.add_argument('--min', type=float, default=-3,
                        help='specifys the minimum value for the PID controller')
    pidControllerOptions.add_argument('--max', type=float, default=3,
                        help='specifys the maximum value for the PID controller')
    pidControllerOptions.add_argument('-D', '--delay', type=float, default=0.0, help='specifys the delay between the PID controller reading the current value and outputting the new value. This is 0 by default')
    
    # logging
    loggingOptions = parentParser.add_argument_group('logging options')
    loggingOptions.add_argument('--log', action='store_true', default=False, help='the program will log the used values if this flag is used. the default file is "log.txt"')
    loggingOptions.add_argument('--log-file', type=Path, default=Path('log.txt'), help='the file used for logging')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='mode', help='the program can use an epics interface or a debug enviroment controlled by another script')
    subparsers.required = True
    
    # normal mode
    pvParser = subparsers.add_parser('normal', help='uses the epics interface', parents=[parentParser])
    pvParser.add_argument('--pv', type=str, default='I1SV02' ,help='the process variable that should be controlled. The default is I1SV02')
    
    # debug mode
    debugParser = subparsers.add_parser('debug', help='uses a test enviroment instead of the epics interface', parents=[parentParser])
    debugParser.add_argument('-f', '--file', type=str, default='debugEnv.txt', help='the text file used for simulating the debug enviroment. The default name is "debugEnv.txt"')
    
    args = parser.parse_args()


    if args.log == True:
        if args.log_file.exists():
            if args.force:
                print('Log file: ' + str(args.log_file) + ' already exists\nOverwriting...')
                remove(args.log_file)
            else:
                print('Log file: ' + str(args.log_file) + ' already exists')
                print('Use the --force flag to overwrite the file')
                print('Exiting...')
                exit()

    args.log_file = str(args.log_file)
    args.file = str(args.file)

    if args.mode == 'debug':
        debugMode(args)
    elif args.mode == 'normal':
        normalMode(args)
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


if __name__ == '__main__':
    main()
