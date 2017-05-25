#!/usr/bin/env python
from csr_aws_guestshell import cag
import argparse

parser = argparse.ArgumentParser(description="Upload tech-support to S3")
parser.add_argument('bucket', help='The name of the bucket to upload to')
parser.add_argument('filename', help='Filename to upload to bucket')
args = parser.parse_args()

bucket = args.bucket
filename = args.filename

cag().save_cmd_output(["show tech-support"], filename, bucket)
