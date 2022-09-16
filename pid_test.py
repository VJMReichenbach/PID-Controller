#!/usr/bin/python3
import epics
from simple_pid import PID
from perlin_noise import PerlinNoise
import argparse
from os import remove

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


def generateNoise(octaves: float = 5, seed: int = 1, xLength: int = 1000):
    """Generates the random dataset with perlin noise"""
    noise = PerlinNoise(octaves=octaves, seed=seed)
    noiseList = []
    for x in range(xLength):
        noiseList.append(noise.noise(x/xLength))
    return noiseList, xLength


def generateData(args, xLength: int = 1000, shift: float = 5):

    shift = int(shift)

    pid = PID(Kp=args.proportional, Kd=args.derivative,
              Ki=args.integral, setpoint=args.niveau)
    pid.sample_time = 1/xLength
    pid.output_limits = (args.min, args.max)

    yControlled = []
    y_i = args.niveau

    for x_i in range(xLength):
        y_i = pid(getCurrentVal(args))
    print(v)
    # TODOOO: alles

def getCurrentVal(args):
    if args.debug == False:
        # TODOOOOOOO: Build testing env
        print('No testing env currently')
        exit()
    else:
        return epics.caget(args.pv)


def debugMode(args):
    try:
        remove("debugEnv.txt")
    except:
        pass
    noise, xLength = generateNoise()
    generateData(args, xLength)


def normalMode(args):
    pv = epics.PV(args.pv)

    # check if the pv is found
    if pv.connected or args.force:
        print(f'PV: {args.pv} connected')
    else:
        print(f'PV: {args.pv} could not connect\nExiting...')
        exit()


    # TODOO: Epics interface
    print('EPICS interface not yet implemented')
    exit()


def main():
    parser = argparse.ArgumentParser(
        description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-p', '--proportional', type=float, default=0.5,
                        help='specifys the coefficient for the proportional term')
    parser.add_argument('-i', '--integral', type=float, default=0.5,
                        help='specifys the coefficient for the integral term')
    parser.add_argument('-d', '--derivative', type=float, default=0,
                        help='specifys the coefficient for the derivative term')
    parser.add_argument('-n', '--niveau', type=float, default=1,
                        help='specifys the niveau that the PID controler should aim for')
    parser.add_argument('--min', type=float, default=-3,
                        help='specifys the minimum value for the PID controller')
    parser.add_argument('--max', type=float, default=3,
                        help='specifys the maximum value for the PID controller')
    parser.add_argument('--force', action='store_true', default=False,
                        help='forces the pv connect check to pass. This is should only be used for development and testing purposes')
    parser.add_argument('--version', action='version', version=ver)

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--pv', type=str,default='I1SV02' ,help='the process variable that should be controlled')
    mode.add_argument('--debug', action='store_true', default=False, help="uses a test enviroment instead of the epics interface")

    args = parser.parse_args()
    
    x = []
    y = []

    
    if args.debug == True:
        debugMode(args)
    else:
        normalMode(args)


if __name__ == '__main__':
    main()
