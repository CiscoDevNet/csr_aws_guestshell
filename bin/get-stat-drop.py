#!/usr/bin/env python
import cli
import re
import argparse

from csr_aws_guestshell import cag

csr = cag()
print_output = 0

def print_cmd_output(command, output):
    if print_output:
        col_space = (80 - (len(command))) / 2
        print "\n%s %s %s" % ('=' * col_space, command, '=' * col_space)
        print "%s \n%s" % (output, '=' * 80)


def execute_command(command):
    cmd_output = cli.execute(command)
    while len(cmd_output) == 0:
        print "CMD FAILED, retrying"
        cmd_output = cli.execute(command)

    print_cmd_output(command, cmd_output)
    return cmd_output


def get_stat_drop():
    cmd_output = execute_command(
        "show platform hardware qfp active statistics drop clear")
    print cmd_output
    if "all zero" in cmd_output:
        csr.send_metric("TailDrop", int(0), "Statistics drops")
        return

    if "TailDrop" not in cmd_output:
        csr.send_metric("TailDrop", int(0), "Statistics drops")

    for line in cmd_output.splitlines():
        if ("-" in line) or ("Global Drop Stats" in line):
            continue

        entries = line.split()
        print "%s --> %s/%s" % (entries[0], entries[1], entries[2])
        csr.send_metric(entries[0], int(entries[1]), "Statistics drops")


def get_datapath_util():
    cmd_output = execute_command(
        "show platform hardware qfp active datapath utilization")

    row_names = [
        "input_priority_pps",
        "input_priority_bps",
        "input_non_priority_pps",
        "input_non_priority_bps",
        "input_total_pps",
        "input_total_bps",
        "output_priority_pps",
        "output_priority_bps",
        "output_non_priority_pps",
        "output_non_priority_bps",
        "output_total_pps",
        "output_total_bps",
        "processing_load_pct"]

    i = 0
    for line in cmd_output.splitlines():
        m = re.search(
            r'.*\s+(?P<fivesecs>\d+)\s+(?P<onemin>\d+)\s+(?P<fivemin>\d+)\s+(?P<onehour>\d+)', line)
        if m:
            # print "%s --> %s %s %s %s" % (row_names[i],
            # m.group('fivesecs'),m.group('onemin'),m.group('fivemin'),m.group('onehour'))
            csr.send_metric(row_names[i], m.group(
                'fivesecs'), "datapath utilization")
            i = i + 1


def show_interface():
    cmd_output = execute_command("show interface summary")
    table_start = 0
    for line in cmd_output.splitlines():
        if 'Interface' in line:
            continue
        if "-" in line:
            table_start = 1
            continue
        if table_start == 0:
            continue
        entries = line.lstrip('*').split()
        cmd = "show interface %s" % (entries[0])
        interface_output = execute_command(cmd)
        m = re.search(
            r'.*\s+(?P<packets_input>\d+) packets input.*\s+(?P<bytes_input>\d+) bytes.*', interface_output)
        if m:
            # print "match! %s %s" %
            # (m.group('packets_input'),m.group('bytes_input'))
            csr.send_metric("packets_input_" +
                            entries[0], m.group('packets_input'), cmd)
            csr.send_metric("bytes_input_" +
                            entries[0], m.group('bytes_input'), cmd)

        m = re.search(
            r'.*\s+(?P<packets_output>\d+) packets output.*\s+(?P<bytes_output>\d+) bytes.*', interface_output)
        if m:
            # print "match! %s %s" %
            # (m.group('packets_output'),m.group('bytes_output'))
            csr.send_metric("packets_output_" +
                            entries[0], m.group('packets_output'), cmd)
            csr.send_metric("bytes_output_" +
                            entries[0], m.group('bytes_output'), cmd)
        m = re.search(
            r'.*\s+(?P<unknown_drops>\d+) unknown protocol drops.*', interface_output)
        if m:
            # print "match! %s" % (m.group('unknown_drops'))
            csr.send_metric("unknown_drops_" +
                            entries[0], m.group('unknown_drops'), cmd)
        m = re.search(
            r'.*Total output drops:\s+(?P<output_drops>\d+)\s+.*', interface_output)
        if m:
            # print "match! %s" % (m.group('output_drops'))
            csr.send_metric("output_drops_" +
                            entries[0], m.group('output_drops'), cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Stats to custom metrics")
    parser.add_argument('--print', help='Print Out ', default=None)
    args = parser.parse_args()

    get_stat_drop()
    get_datapath_util()
    show_interface()
