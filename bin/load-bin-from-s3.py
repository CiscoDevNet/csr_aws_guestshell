#!/usr/bin/env python
import cli
from csr_aws_guestshell import cag
import argparse

parser = argparse.ArgumentParser(description="Upload bin file")
parser.add_argument('bucket', help='The name of the bucket to upload to')
parser.add_argument('filename', help='Filename to upload to bucket')
parser.add_argument('--reload', help='After downloading, reboot system', default=None)
args = parser.parse_args()

bucket = args.bucket
filename = args.filename

cag().download_file(bucket, filename)

configuration = "boot system flash:" + filename
cli.configure(configuration)
cli.execute("copy running start")
if args.reload is not None:
    cli.execute("reload")
