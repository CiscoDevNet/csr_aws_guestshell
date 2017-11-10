#!/usr/bin/env python
import cli
from csr_aws_guestshell import cag
import argparse

parser = argparse.ArgumentParser(description="Download Config file")
parser.add_argument('bucket', help='The name of the bucket to download from')
parser.add_argument('filename', help='Filename to download from bucket')
args = parser.parse_args()

bucket = args.bucket
filename = args.filename

cag().download_file(bucket, filename)

cli.execute("copy bootflash:%s running-config" % filename)
