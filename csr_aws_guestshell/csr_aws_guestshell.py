#!/usr/bin/env python
import boto3
import sys
import threading
import cli
from boto.utils import get_instance_metadata
import syslog


class cag():
    def __init__(self):
        self.s3_resource = boto3.resource('s3')
        self.s3_client = boto3.client('s3')
        self.cloudwatch = boto3.client('cloudwatch')
        self.metadata = self.get_metadata()
        self.instance_id = "Not Found"
        if self.metadata:
            self.instance_id = self.metadata['instance-id']

    class ProgressPercentage(object):
        def __init__(self, filename, cag):
            self._filename = filename

            self.itemtocheck = cag.s3_resource.ObjectSummary(
                cag.bucket, cag.filename)
            self._size = self.itemtocheck.size

            self._seen_so_far = 0
            self._lock = threading.Lock()

        def __call__(self, bytes_amount):
            with self._lock:
                self._seen_so_far += bytes_amount
                percentage = (float(self._seen_so_far) * 100 / self._size)

                sys.stdout.write(
                    "\r%s  %s / %d  (%.2f%%)" % (
                        self._filename, int(self._seen_so_far), self._size,
                        percentage))
                sys.stdout.flush()

    def download_file(self, bucket, filename, directory="/bootflash/"):
        self.bucket = bucket
        self.filename = filename
        try:
            self.s3_client.download_file(
                bucket, filename, directory + filename, Callback=self.ProgressPercentage(directory + filename, self))
        except Exception as e:
            print "Downloading file Failed.  Error: %s" % (e)
            return False
        print "\nDownload Complete"
        return True

    def upload_file(self, bucket, filename, directory="/bootflash/"):

        try:
            self.s3_client.upload_file(directory + filename, bucket, filename)
        except Exception as e:
            print "Uploading file Failed.  Error: %s" % (e)
            return False
        print "Upload Complete to S3 bucket %s" % (bucket)
        return True

    def save_cmd_output(self, cmdlist, filename, bucket=None, directory="/bootflash/", print_output=False):

        with open(directory + filename, 'w') as f:
            for command in cmdlist:
                cmd_output = cli.execute(command)
                col_space = (80 - (len(command))) / 2
                if print_output is True:
                    print "\n%s %s %s" % ('=' * col_space, command, '=' * col_space)
                    print "%s \n%s" % (cmd_output, '=' * 80)

                f.write("\n%s %s %s\n" %
                        ('=' * col_space, command, '=' * col_space))
                f.write("%s \n%s\n" % (cmd_output, '=' * 80))
        if bucket is not None:
            self.upload_file(bucket, filename)

    def send_metric(self, name, value, category):
        value = int(value)
        message = "category: %s: name: %s, value %d" % (category, name, value)
        syslog.syslog(message)
        response = self.cloudwatch.put_metric_data(
            Namespace="csr1000v",
            MetricData=[{'MetricName': name,
                         'Value': value,
                         'Unit': 'Count',
                         'Dimensions': [
                             {
                                 "Name": "PerInstanceStatistics",
                                 "Value": category,
                                 "Name": "Instance-id",
                                 "Value": self.instance_id
                             }
                         ],
                         }
                        ],
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print "Error sending %s" % name

    def get_metadata(self):
        return get_instance_metadata(timeout=2, num_retries=1)
