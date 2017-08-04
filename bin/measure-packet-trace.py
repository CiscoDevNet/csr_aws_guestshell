#!/usr/bin/env python
import cli
import sys
import argparse
import time
import re
from collections import defaultdict
import csv

parser = argparse.ArgumentParser(
    description="Enable Packet trace and measure time for FIA")
parser.add_argument(
    '--clear', help='do not clear of packet trace statistics', default=1)
parser.add_argument(
    '--filename', help='name of csv file to export values to', default="packet-trace.csv")
parser.add_argument('--pktnum', help='print details on pktnum', default=None)
parser.add_argument('--seconds', help='Seconds to capture', default=1)
parser.add_argument('--showonly', help='operate on previous list', default=0)
parser.add_argument(
    '--pktbypkt', help='retrieve packet by packet', default=True)
parser.add_argument(
    '--pktcnt', help='number of packets to capture', default=128, type=int)

args = parser.parse_args()

if args.showonly == 0 and args.pktnum is None:
    print "executing CLI..."

    if args.clear is not None:
        cli.execute("clear platform packet-trace config")
        cli.execute("clear platform packet-trace statistics")
    cli.execute("debug platform condition both")
    cli.execute(
        "debug platform packet-trace packet %u fia-trace data-size 2048" % (args.pktcnt))
    cli.execute("debug platform condition start")

    for i in range(0, int(args.seconds)):
        time.sleep(1)
        sys.stdout.write("\r%d secs" % (i + 1))
        sys.stdout.flush()

    print "\n"

    cli.execute("debug platform condition stop")

print "retrieving CLI..."


if args.pktbypkt is False:
    output = cli.execute("show platform packet-trace packet all decode")
else:
    output = ""
    pkt_num = 0
    while True:
        cmd = cli.execute(
            "show platform packet-trace packet %d decode | inc (Packet|Start|Stop|Feature|Lapsed)" % (pkt_num))
        if "Invalid" in cmd or len(cmd) == 0:
            break
        output += (cmd + "\n")
        pkt_num = pkt_num + 1
    print "Retrieved %d packets" % pkt_num


features = defaultdict(list)
packets = {}
times = []
feature_lines = []
packet_line = []
start_time = stop_time = ""
total_time = 0
packet_num = 0

print "Parsing data..."

for line in output.splitlines():
    if "Packet" in line:
        m = re.search(r'\bPacket: (?P<packet_num>\d+).*', line)
        if m:
            new_packet_num = m.group('packet_num')

            if len(stop_time):
                total_time = (int(stop_time) - int(start_time))
                times.append((packet_num, total_time))
                packets[packet_num] = packet_line
            packet_num = new_packet_num
            stop_time = ""
            packet_line = []

    if "Feature:" in line:
        feature_name = line.split(":")[1]
        feature_lines = []

    if "Lapsed time" in line:
        lapsed_time = int(line.split(":")[1].split()[0])

        features[feature_name].append(
            (packet_num, lapsed_time, feature_lines))

    feature_lines.append(line)
    packet_line.append(line)

    if "Start" in line:
        start_time = line.split(":")[1].split()[0]

    if "Stop" in line:
        stop_time = line.split(":")[1].split()[0]

if args.pktnum is not None:
    if args.pktnum in packet_line:
        for line in packet_line[args.pktnum]:
            print line
        sys.exit(1)

print "Sorting data..."

time_sorted = sorted(times, key=lambda x: x[1])
if len(time_sorted) > 0:
    max_time_packet = time_sorted[-1][0]
    print "Min time is packet %s, value %d" % (time_sorted[0][0], time_sorted[0][1])
    print "Max time is packet %s, value %d" % (max_time_packet, time_sorted[-1][1])
    average = float(sum(n for _, n in time_sorted)) / len(time_sorted)

# print "Max Packet:"
# for line in packets[max_time_packet]:
#    print line

print "Storing list..."
data_list = []
for feature, tuple_list in features.iteritems():
    cnt = len(tuple_list)
    total = sum([t[1] for t in tuple_list])
    pkt_num = t[0]
    average = int(float(total) / cnt)
    minimum = min(tuple_list, key=lambda item: item[1])
    maximum = max(tuple_list, key=lambda item: item[1])
    median = sorted([(lambda x: x[1])(x) for x in tuple_list])[int(cnt / 2)]
    data_list.append((feature, cnt, pkt_num, minimum[
                     1], maximum[1], median, average))


data_sorted = sorted(data_list, key=lambda x: x[5], reverse=True)

print "Printing list..."

print "%-40s %10s %10s %10s %10s %10s %10s" % ("Feature", "Count", "Packet", "Min", "Max", "Avg", "Med")
print "-" * 106
for entry in data_sorted:
    feature = entry[0]
    cnt = entry[1]
    pkt_num = entry[1]
    minimum = entry[2]
    minimum = entry[3]
    maximum = entry[4]
    median = entry[5]
    average = entry[6]
    print "%-40s %10s %10d %10s %10s %10s %10s" % (feature, cnt, pkt_num, minimum, maximum, average, median)

with open('/bootflash/' + args.filename, 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',
                           quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(
        ["Feature Name", "Count", "Packet Number", "Minimum", "Maximum", "Average", "Median"])
    for entry in data_sorted:
        feature = entry[0]
        cnt = entry[1]
        pkt_num = entry[2]
        minimum = entry[3]
        maximum = entry[4]
        median = entry[5]
        average = entry[6]
        csvwriter.writerow(
            [feature, cnt, pkt_num, minimum, maximum, average, median])

    csvwriter.writerow(["Feature Name", "Packet Number", "Lapsed time"])
    for feature, tuple_list in features.iteritems():
        for t in tuple_list:
            csvwriter.writerow([feature, t[0], t[1]])

    for i, pkt in packets.iteritems():
        for line in pkt:
            csvwriter.writerow([line])
