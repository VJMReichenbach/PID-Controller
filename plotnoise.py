#!/usr/bin/python3
from epics import caget
import matplotlib.pyplot as plt
import argparse
from time import time, asctime

def main(args):
    x = []
    y1 = []
    y2 = []

    plt.ion()

    graph_len = args.graph_len
    start_time = time()

    if not args.no_log:
        f = open(args.log_file, "w")
        f.write("Time\t\t\t\tPV1: " + args.pv1 + "\t\tPV2: " + args.pv2 + "\n")
    try:
        while True:
            x.append(time() - start_time)
            y1_val = caget(args.pv1 + ":outCur")
            y2_val = caget(args.pv2 + ":outCur")
            y1.append(y1_val)
            y2.append(y2_val)
            if not args.no_delete and len(x) > graph_len:
                x.pop(0)
                y1.pop(0)
                y2.pop(0)

            if not args.no_log:
                f.write(asctime() + "\t" + str(y1_val) + "\t\t" + str(y2_val) + "\n")

            plt.cla()

            plt.title("Noise")
            plt.plot(x, y1, label=args.pv1)
            plt.plot(x, y2, label=args.pv2)
            plt.xlabel("Time (s)")
            plt.ylabel("Current (A)")
            plt.legend()
            plt.pause(0.1)
    except KeyboardInterrupt:
        print("Exiting")

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Plot noise from EPICS')
    parser.add_argument('pv1', type=str, help='PV name 1')
    parser.add_argument('pv2', type=str, help='PV name 2')
    parser.add_argument('--graph_len', type=int, default=1000, help='Length of graph (default: 1000)')
    parser.add_argument('--no-delete', action='store_true', help='Do not delete old data')
    parser.add_argument('--no-log', action='store_true', help='Do not log data')
    parser.add_argument('--log-file', type=str, default='plot_noise_log.txt', help='Log file name (default: plot_noise_log.txt)')


    args = parser.parse_args()

    main(args)
