#!/usr/bin/python3
from os import remove
import epics
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

def getCurrentVal(args, debugFile: Path=Path('debugEnv.txt')) -> float:
    if args.mode == 'debug':
        # Check if the debug file exists
        try:
            f = open(debugFile, 'r')
            val = f.read()
            f.close()
        except Exception as e:
            print('The debug file ' + debugFile + ' was not found')
            print('Exception: ', e)
            print('Exiting...')
            exit()
        
        # BUG: sometimes nothing is read when not in v mode
        try:
            val = float(val)
        except Exception as e:
            if args.verbose >= 1:
                print('couldn\'t convert val: "' + val + '" to float. Returned 0 instead')
            if args.verbose >= 2:
                print('Exception: ', e)
            val = 0

        return val
    elif args.mode == 'normal':
        # TODO: check pv name
        return epics.caget(f'{args.pv}:outCur')
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


def debugMode(args):
    debugFile = Path('./' + args.file)
    args.pv = 'debug'
    getCurrentVal(args=args, debugFile=debugFile)
    # TODOO: find sample time and parameters
    pid = PID(Kp=args.proportional, Kd=args.derivative, Ki=args.integral, setpoint=args.niveau)
    # pid.sample_time = 0.0005
    # pid.output_limits = (args.min, args.max)

    x = []
    y1 = []
    y2 = []

    plt.ion() # plot all graphs in the same window

    startTime = time()

    graphLen = 80

    # log options
    if args.log == True:
        logFile = Path(args.log_file)
        header = 'PID-Controller Log File\nPV: ' + args.pv + '\nKp: ' + args.proportional + '\nKi: ' + args.integral + '\nKd: ' + args.derivative + '\nNiveau: ' + args.niveau + '\nDelay: ' + args.delay + '\n\n'
        with open(logFile, 'w') as l:
            l.write(header)
            l.write('time, corrected Value, current Value\n')
            l.close()

    try:
        while True:
            currentVal = getCurrentVal(args=args, debugFile=debugFile)

            # get new value
            correctVal = float(pid(currentVal))

            # wrtie new value to debug file
            f = open(debugFile, 'w')
            f.write(str(correctVal))
            f.close()

            if args.verbose >= 2:
                print('time: ' + time()-startTime + ', corrected Value: ' + correctVal + ', current Value: ' + currentVal + '')

            if args.log == True:
                logFile = Path(args.log_file)
                l = open(logFile, 'a')
                l.write(str(time() - startTime) + ', ' + str(correctVal) + ', ' + str(currentVal) + '\n')
                l.close()
            
            
            # plotting
            if args.visualize == True:

                x.append(time() - startTime)
                y1.append(correctVal)
                y2.append(args.niveau)

                # makes sure that the graph doesnt grow infinitly
                if len(x) >= graphLen:
                    x.pop(0)
                if len(y1) >= graphLen:
                    y1.pop(0)
                if len(y2) >= graphLen:
                    y2.pop(0)

                plt.cla() # clear axes

                plt.title('correct: ' + str(correctVal))
                plt.plot(x, y1, label='Value')
                plt.plot(x, y2, label='Niveau')
                plt.legend(loc='upper left')

                plt.pause(0.1)

            sleep(args.delay)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        #TODO: necessary cleanup?
        exit()




def normalMode(args):
    pv = epics.PV(args.pv)

    # check if the pv is found
    if pv.connected or args.force:
        print('PV: ' + args.pv + ' connected')
    else:
        print('PV: ' + args.pv + ' not found')
        print('Exiting...')
        exit()

    # TODOOOOOO: umrechnung von pos zu strom
    # TODOOO: Epics interface
    print('EPICS interface not yet implemented')
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
                print('Log file: ' + args.log_file + ' already exists\nOverwriting...')
                remove(args.log_file)
            else:
                print('Log file: ' + args.log_file + ' already exists')
                print('Use the --force flag to overwrite the file')
                print('Exiting...')
                exit()

    if args.mode == 'debug':
        debugMode(args)
    elif args.mode == 'normal':
        normalMode(args)
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


if __name__ == '__main__':
    main()
