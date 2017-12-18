#!/usr/bin/python
import cli
import argparse

from csr_aws_guestshell import cag


def print_cmd_output(command, output):
    col_space = (80 - (len(command))) / 2
    print "\n%s %s %s" % ('=' * col_space, command, '=' * col_space)
    print "%s \n%s" % (output, '=' * 80)


def execute_command(command, print_output):
    cmd_output = cli.execute(command)
    while len(cmd_output) == 0:
        print "CMD FAILED, retrying"
        cmd_output = cli.execute(command)

    if print_output:
        print_cmd_output(command, cmd_output)
    return cmd_output


def get_tunnel_number(print_output):
    csr = cag()

    cmd_output = execute_command(
        "show ip interface brief | in Tunnel", print_output)

    TunnelNumber = 0
    for line in cmd_output.splitlines():
        entries = line.split()
        if entries[4] == "up" and entries[5] == "up":
            TunnelNumber += 1

    print "TunnelNumber is %s" % (TunnelNumber)
    csr.send_metric("TunnelNumber", TunnelNumber, "VPN Status")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload VPN Status to Cloudwatch")
    parser.add_argument('--print_output', help='Print output ', action='store_true')
    args = parser.parse_args()

    get_tunnel_number(args.print_output)
