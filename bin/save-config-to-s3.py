#!/usr/bin/env python
import cli
from csr_aws_guestshell import cag
import argparse

parser = argparse.ArgumentParser(description="Upload config file")
parser.add_argument('bucket', help='The name of the bucket to upload to')
parser.add_argument('filename', help='Filename to upload to bucket')
args = parser.parse_args()

bucket = args.bucket
print args.filename
filename = str(args.filename).strip()
print filename
# first, save the config to bootflash
get_config = "copy running-config bootflash:%s" % filename
result = cli.execute(get_config)
result = result.splitlines()

# print output of ios cli output showing the config copy
for line in result:
        if 'copied' in line:
                print line

cag().upload_file(bucket, filename)
