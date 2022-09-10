#!/usr/bin/python3

from simple_pid import PID
import matplotlib.pyplot as plt
from perlin_noise import PerlinNoise
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

def generateNoise(octaves: float=5, seed: int=1):
    """Generates the random dataset with perlin noise"""
    noise = PerlinNoise(octaves=octaves, seed=seed)
    xP = 10
    yP = 10
    for x in range(0,9):
        for y in range(0,9):
            print(noise.noise([x/xP, y/yP]))
    return 0

def generateData(args):
    pid = PID(Kp=args.proportional, Kd=args.derivative, Ki=args.integral, setpoint=args.niveau)

def debugMode(args):
    generateNoise()
    generateData(args)

def normalMode(args):
    # TODOO: Epics interface
    print('EPICS interface not yet implemented')
    exit()

def main():
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-p', '--proportional',type=float, default=0.5, help='specifys the coefficient for the proportional term')
    parser.add_argument('-i', '--integral',type=float, default=0.5, help='specifys the coefficient for the integral term')
    parser.add_argument('-d', '--derivative',type=float, default=0, help='specifys the coefficient for the derivative term')
    parser.add_argument('-n', '--niveau', type=float, default=1, help='specifys the niveau that the PID controler should aim for')
    parser.add_argument('--debug', action='store_true', default=False, help="uses a test enviroment instead of the epics interface")
    parser.add_argument('--version', action='version', version=ver)


    args = parser.parse_args()

    if args.debug == True:
        debugMode(args)
    else:
        normalMode(args)

    
if __name__ == '__main__':
    main()