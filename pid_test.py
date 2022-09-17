#!/usr/bin/python3
from cProfile import label
import graphlib
from lib2to3.pgen2.token import RPAR
import epics
from simple_pid import PID
from perlin_noise import PerlinNoise
import argparse
from pathlib import Path
from time import sleep, time
import matplotlib.pyplot as plt

ver = "0.1.0"
author = "Valentin Reichenbach"
description = f"""
TODO: Insert description
"""
epilog = f"""
Author: {author}
Version: {ver}
License: GPLv3+
"""    

def getCurrentVal(args, debugFile: Path=Path('debugEnv.txt')) -> float:
    if args.mode == 'debug':
        f = open(debugFile, 'r')
        val = f.read()
        f.close()
        # BUG: sometimes nothing is read when not in v mode
        try:
            val = float(val)
        except Exception as e:
            if args.verbose >= 1:
                print(f'couldn\'t convert val: "{val}" to float. Returned 0 instead')
            if args.verbose >= 2:
                print('Exception: ', e)
            val = 0

        return val
    elif args.mode == 'normal':
        # TODOO: check pv name
        return epics.caget(f'{args.pv}:outCur')
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


def debugMode(args):
    # TODOOOOOOOOOOOO: write debug mode
    debugFile = Path('./' + args.file)
    getCurrentVal(args=args, debugFile=debugFile)
    pid = PID(Kp=args.proportional, Kd=args.derivative, Ki=args.integral, setpoint=args.niveau)
    # TODOO: find sample time
    # pid.sample_time = 0.0005
    # pid.output_limits = (args.min, args.max)

    x = []
    y1 = []
    y2 = []

    plt.ion() # plot all graphs in the same window

    startTime = time()

    graphLen = 40

    try:
        while True:
            currentVal = getCurrentVal(args=args, debugFile=debugFile)
            correctVal = pid(currentVal)
            f = open(debugFile, 'w')
            f.write(str(correctVal))
            f.close()
            
            
            # plotting
            if args.visulize == True:

                plt.title('correct: ' + str(correctVal))

                if args.verbose >= 2:
                    print(f'time: {time()-startTime}, corrected Value: {currentVal}, current Value: {currentVal}')

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

                plt.plot(x, y1, label='Value')
                plt.plot(x, y2, label='niveau')
                plt.legend(loc='upper left')

                plt.pause(0.1)
    except KeyboardInterrupt:
        print('\nKeyboard interrupt detected\nExiting...')
        #TODO: necessary cleanup?
        exit()




def normalMode(args):
    pv = epics.PV(args.pv)

    # check if the pv is found
    if pv.connected or args.force:
        print(f'PV: {args.pv} connected')
    else:
        print(f'PV: {args.pv} could not connect\nExiting...')
        exit()


    # TODOOO: Epics interface
    print('EPICS interface not yet implemented')
    exit()


def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter) 
    
    parentParser = argparse.ArgumentParser('The Parrent parser', add_help=False)
    
    # general options
    parentParser.add_argument('--visulize', action='store_true', default=False, help='visulize the changed values live')
    parentParser.add_argument('-p', '--proportional', type=float, default=0.7,
                        help='specifys the coefficient for the proportional term')
    parentParser.add_argument('-i', '--integral', type=float, default=0.3,
                        help='specifys the coefficient for the integral term')
    parentParser.add_argument('-d', '--derivative', type=float, default=0,
                        help='specifys the coefficient for the derivative term')
    parentParser.add_argument('-n', '--niveau', type=float, default=1,
                        help='specifys the niveau that the PID controler should aim for')
    parentParser.add_argument('--min', type=float, default=-3,
                        help='specifys the minimum value for the PID controller')
    parentParser.add_argument('--max', type=float, default=3,
                        help='specifys the maximum value for the PID controller')
    parentParser.add_argument('--version', action='version', version=ver)
    parentParser.add_argument('-v', '--verbose', action='count', default=0, help='verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='mode', help='the program can use an epics interface or a debug enviroment controlled by another script')
    subparsers.required = True
    
    # normal mode
    pvParser = subparsers.add_parser('normal', help='uses the epics interface', parents=[parentParser])
    pvParser.add_argument('--pv', type=str, default='I1SV02' ,help='the process variable that should be controlled. The default is I1SV02')
    pvParser.add_argument('--force', action='store_true', default=False,
                        help='forces the pv connect check to pass. This is should only be used for development and testing purposes')
    
    # debug mode
    debugParser = subparsers.add_parser('debug', help='uses a test enviroment instead of the epics interface', parents=[parentParser])
    debugParser.add_argument('-f', '--file', type=str, default='debugEnv.txt', help='the text file used for simulating the debug enviroment. The default name is "debugEnv.txt"')
    
    args = parser.parse_args()

    
    if args.mode == 'debug':
        debugMode(args)
    elif args.mode == 'normal':
        print(args)
        normalMode(args)
    else:
        print('Something went wrong while parsing the arguments\nExiting...')
        exit()


if __name__ == '__main__':
    main()
