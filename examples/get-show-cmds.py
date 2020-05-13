#!/usr/bin/env python
from __future__ import print_function
from builtins import *
from csr_aws_guestshell import cag
import argparse

cmdlist = \
    [
        "show interfaces",
        "show version",
        "show ip route",
        "show platform hardware qfp active statistics drop",
        "show platform hardware qfp active datapath utilization",
        "show interfaces gigabitEthernet 1 | incl drops|pack|err",
        "show platform hardware throughput level",
    ]


parser = argparse.ArgumentParser(description="Upload test file")
parser.add_argument('bucket', help='The name of the bucket to upload to')
parser.add_argument('filename', help='Filename to upload to bucket')
args = parser.parse_args()


cag().save_cmd_output(cmdlist, args.filename, args.bucket)
