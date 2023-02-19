#!/usr/bin/python3
import numpy as np
import argparse
from pathlib import Path
from time import sleep

ver = "1.0.0"
author = "Valentin Reichenbach"
description = f"""
Generates a sine wave and writes it to a file.
"""
epilog = f"""
Author: {author}
Version: {ver}
License: GPLv3+
"""    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--frequency", help="Frequency of the sine wave in Hz. Default is 50", type=int, default=50)
    parser.add_argument("-o", "--output", help="Output file. Default is sin.txt", default=Path("sin.txt"))
    parser.add_argument("-F", "--force", help="Force overwrite of output file", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="count", default=0)
    parser.add_argument("-V", "--version", help="Print version and exit", action="version", version=ver)
    args = parser.parse_args()

    x = 0 # in radians
    if args.frequency < 0:
        print("Frequency must be positive")
        exit(1)
    
    if args.output.exists():
        if args.force:
            print(f"Overwriting {args.output}")
        else:
            print(f"File {args.output} already exists. Use -F to force overwrite")
            exit(1)
    else:
        print(f"Writing to {args.output}")

    try:
        while True:
            # Generate sine wave
            y = np.sin(2 * np.pi * args.frequency * x)
            x = (x + args.frequency / 2*np.pi) % 2 * np.pi

            if args.verbose > 0:
                print(f"Frequency: {args.frequency}Hz, x: {x}, y: {y}")

            sleep(1/args.frequency)

            # Write to file
            with open(args.output, "w") as f:
                f.write(f"{y}")

    except KeyboardInterrupt:
        print("\n Keyboard interrupt")
        print("Exiting...")
        f.close()
        exit(0)
