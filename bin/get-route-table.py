#!/usr/bin/env python
import sys
import getopt
import json
import boto3
from boto.utils import get_instance_metadata

ec2 = boto3.resource('ec2')
client = boto3.client('ec2')
dump_json = 0
eni = ""
subnet_to_route_table = {}


def print_instance_header():
    print "%-30s %-20s %-10s %-15s %-15s %-15s %-10s %-20s" % ("Name", "id", "type", "nametag", "private ip", "Public ip", "state", "launch time")
    print "-" * 140


def print_instance_info(i):
    instance_name = ''
    if i.tags is not None:
        for tags in i.tags:
            if tags["Key"] == 'Name':
                instance_name = tags["Value"]

    # if 'Name' in i.tags:
    #     instance_name = i.tags['Name']
    print "%-30s %-20s %-10s %-15s %-15s %-15s %-10s %-20s" % \
        (instance_name[:30], i.id, i.instance_type, i.image_id,
         i.private_ip_address, i.public_ip_address, i.state['Name'], i.launch_time)


def print_metadata_info(metadata):
    region = metadata['placement']['availability-zone'][:-1]
    instance_id = metadata['instance-id']
    print "Region is %s, Instance Id is %s" % (region, instance_id)
    if dump_json:
        print json.dumps(metadata, sort_keys=True, indent=2)


def print_vpc_header(vpc_id):
    sidecnt = (140 - len(vpc_id)) / 2
    print "\n" * 2 + "=" * sidecnt + vpc_id + "=" * sidecnt
    print "%-20s %-15s %-10s %-15s %-15s %-15s %-15s %-15s %-15s" % \
        ("Name", "vpc-id", "state", "ipv4-cidr", "ipv6-cidr",
         "DHCP options", "Route Table", "Network ACL", "Tenancy")
    print "-" * 140


def print_vpc_info(vpc):
    route_tables = vpc.route_tables.all()

    # print route_tables
    for route in route_tables:
        for r in route.routes:
            if r.destination_cidr_block == "0.0.0.0/0":
                route_tbl = route.route_table_id

    vpc_name = ''
    if vpc.tags is not None:
        for tags in vpc.tags:
            if tags["Key"] == 'Name':
                vpc_name = tags["Value"]

    network_acl_iterator = vpc.network_acls.all()
    for acl in network_acl_iterator:
        acl_id = acl.id

    ipv6_cidr = "[]"
    if vpc.ipv6_cidr_block_association_set is not None:
        for ipv6 in vpc.ipv6_cidr_block_association_set:
            ipv6_cidr = ipv6['Ipv6CidrBlock']
    if vpc.is_default:
        default = "*" + vpc.id
    else:
        default = vpc.id
    print "%-20s %-15s %-10s %-15s %-15s %-15s %-15s %-15s %-15s" % \
        (vpc_name[:30], default, vpc.state, vpc.cidr_block, ipv6_cidr,
         vpc.dhcp_options_id, route_tbl, acl_id, vpc.instance_tenancy)


def print_route_info(vpc):
    global eni
    global subnet_to_route_table
    # get all routes on subnet
    subnet = ""
    rtb_assoc_id = ""

    resp_rt_table = client.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc.id,
                ]
            },
        ])
    if dump_json:
        print(json.dumps(resp_rt_table, indent=2))

    print "\n* -- interface on this instance"
    print "%-20s %-20s %-20s %-20s %-20s %-20s %-20s" % \
        ("Route Table", "Destination", "Target",
         "Status", "Assoc id", "subnet", "Propagated")
    print "-" * 140

    for r in (resp_rt_table['RouteTables']):
        for a in r['Associations']:
            if a['Main']:
                subnet_to_route_table['default'] = a['RouteTableId']
        for a in r['Associations']:
            rtb_assoc_id = a['RouteTableAssociationId']
            if 'SubnetId' in a:
                subnet = a['SubnetId']
                subnet_to_route_table[subnet] = a['RouteTableId']
            else:
                subnet = ""

        if r['PropagatingVgws'] is None:
            propagated = "No"
        else:
            propagated = "Yes"

        for route in r['Routes']:
            gateway = ""
            if 'GatewayId' in route:
                gateway = route['GatewayId']
            else:
                if 'NetworkInterfaceId' in route:
                    gateway = route['NetworkInterfaceId']
                    if eni == gateway:
                        gateway = "*" + gateway
            if 'DestinationCidrBlock' in route:
                destinationblock = route['DestinationCidrBlock']
            else:
                destinationblock = "NoCidr"
            print "%-20s %-20s %-20s %-20s %-20s %-20s %-20s" % \
                (r['RouteTableId'], destinationblock,
                 gateway, route['State'], rtb_assoc_id, subnet, propagated)


def print_subnet_info(vpc):
    global subnet_to_route_table

    subnets = vpc.subnets.all()

    print "\n%-20s %-10s %-15s %-15s %-15s %-20s %-20s %-20s" % \
        ("subnet-id", "state", "vpc-id", "ipv4-cidr",
         "Available ipv4", "ipv6 cidr", "Avail. Zone", "Route Table")
    print "-" * 140

    for snet in subnets:
        if snet.id in subnet_to_route_table:
            route_table = subnet_to_route_table[snet.id]
        else:
            route_table = subnet_to_route_table['default']
        print "%-20s %-10s %-15s %-15s %-15s %-20s %-20s %-20s" % \
            (snet.id, snet.state, snet.vpc_id, snet.cidr_block, snet.available_ip_address_count,
             snet.ipv6_cidr_block_association_set, snet.availability_zone, route_table)


def get_vpc_info(vpc_id):
    vpc = ec2.Vpc(vpc_id)

    print_vpc_info(vpc)

    # find all instances in our vpc.
    vpclist = vpc.instances.all()
    instance_count = sum(1 for _ in vpclist)
    if (instance_count):
        print "\nVpc %s has %s instances" % (vpc_id, instance_count)
        print_instance_header()
    for instance in vpclist:
        print_instance_info(instance)

    # get all subnets on vpc
    print_route_info(vpc)
    print_subnet_info(vpc)


def print_help():
    print('-j       --- output json from commands')


def main(argv):
    global eni
    if len(sys.argv) > 1:
        try:
            opts, args = getopt.getopt(argv, "j", [
                                       "json"])
        except getopt.GetoptError:
            print_help()
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-j"):
                global dump_json
                dump_json = 1
    # our instance
    print "Determining if we are running on AWS..."
    metadata = get_instance_metadata(timeout=2, num_retries=1)

    if metadata:
        print_metadata_info(metadata)

        for mac in metadata["network"]["interfaces"]["macs"]:
            vpc_info = metadata["network"]["interfaces"]["macs"][mac]
            eni = vpc_info["interface-id"]
            vpc_id = vpc_info["vpc-id"]

            print "VPC: %s ENI %s" % (vpc_id, eni)
            print_vpc_header(vpc_id)
            get_vpc_info(vpc_id)
    else:
        response = client.describe_vpcs()

        for vpc_client in response["Vpcs"]:
            vpc_id = vpc_client['VpcId']
            print_vpc_header(vpc_id)
            get_vpc_info(vpc_id)

if __name__ == "__main__":
    main(sys.argv[1:])
