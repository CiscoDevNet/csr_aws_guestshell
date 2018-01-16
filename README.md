# Scripts for guestshell on Cisco CSR1000V on AWS

## Introduction

This repository contains a library (csr_aws_guestshell) that has helper functions to make script writing a bit easier for AWS.

## Installation 

To enable guestshell on CSR on AWS:
```
ios-prompt#  guestshell enable VirtualPortGroup 0 guest-ip 192.168.35.2 name-server 8.8.8.8
Please wait for completion
ios-prompt# guestshell

```

To install csr_aws_guestshell:

```
[guestshell@guestshell ~]$ sudo pip install csr_aws_guestshell
```
Alternatively, you can install to your user directory:
```
[guestshell@guestshell ~]$ pip install --user csr_aws_guestshell
```

## Running scripts 

Scripts will be copied to the guestshell $PATH where they can then be run.  

List of scripts to be installed:
* [```get-metadata.py```](bin/get-metadata.py) -- retrieves instance metadata and prints to stdout
* [```get-route-table.py```](bin/get-route-table.py) -- retrieves route table information including instances in vpc and route table associations
* [```save-config-to-s3.py```](bin/save-config-to-s3.py) -- saves CSR1000V config to bootflash and uploads to AWS S3 bucket
* [```save-tech-support-to-s3.py```](bin/save-tech-support-to-s3.py) -- saves CSR1000V tech-support output to bootflash and uploads to AWS S3 bucket
* [```load-bin-from-s3.py```](bin/load-bin-from-s3.py) -- copies CSR1000V config from S3 to bootflash and then copies to running-config
* [```measure-packet-trace.py```](bin/measure-packet-trace.py) -- Enables packet trace via CLI, retrieves results, and sorts based on longest execution
* [```get-stat-drop.py```](bin/get-stat-drop.py) -- Retrieves statistics from cli and publishes them to Cloudwatch
* [```monitor-vpn.py```](bin/monitor-vpn.py) -- Uploads Number of Tunnels that are up to Cloudwatch

## Example output from running via IOS shell:

```
ip-172-31-52-111#guestshell run get-metadata.py
{
    "ami-id": "ami-1234abcd", 
    "ami-launch-index": "0", 
    "ami-manifest-path": "(unknown)", 
    "block-device-mapping": {
        "ami": "/dev/xvda", 
        "root": "/dev/xvda"
    }, 
    "hostname": "ip-XXX-XX-XX-XXX.ec2.internal", 

     ... <snip> ...

```

## Example output from running via guestshell prompt:

```
[guestshell@guestshell ~]$ get-metadata.py
{
    "ami-id": "ami-1234abcd", 
    "ami-launch-index": "0", 
    "ami-manifest-path": "(unknown)", 
    "block-device-mapping": {
        "ami": "/dev/xvda", 
        "root": "/dev/xvda"
    }, 
    "hostname": "ip-XXX-XX-XX-XXX.ec2.internal", 

     ... <snip> ...
```

## Examples using cli module

These scripts make use of the cli.py script pre-installed to guestshell.  there are 4 main functions to use with the cli module:

```
import cli
show_run_output = cli.execute("show run")
```

Alternatively, you can print the result to stdout:
```
import cli
cli.executep("show run")
```

```
import cli
file = my_file.py
cron_entry="\"*/%d * * * *\"" % (seconds)
gs_cmd="\"guestshell run %s\"" % (file)

configuration = '''event manager applet %s
                        action 1.0 cli command %s
                        event timer cron cron-entry %s''' % (file,gs_cmd,cron_entry)
result= cli.configure(configuration)
```


```
import cli
cli.configurep("copy running-config startup-config")
```

## Library "helpers"

These scripts contain the following functions to assist in script development:

* ```download_file``` -- called with bucket name, filename and optional directory for the destination on the CSR1000V
* ```upload_file``` -- called with bucket name, filename and optional directory for the location on the CSR1000V
* ```save_cmd_output``` -- called with command list via python list, filename to save to, optional bucket if uploading file, and flag to print to stdout

## Examples using csr_aws_guestshell

```
from csr_aws_guestshell import cag

cag().upload_file(my_bucket, my_filename)

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
cag().save_cmd_output(cmdlist, my_filename, my_bucket)
```
